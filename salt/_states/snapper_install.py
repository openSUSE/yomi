# Copyright (c) 2019 SUSE LINUX GmbH, Nuernberg, Germany.

# This file is part of Salt-autoinstaller.

# Salt-autoinstaller is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Salt-autoinstaller is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Salt-autoinstaller.  If not, see <https://www.gnu.org/licenses/>.

'''
:maintainer:    Alberto Planas <aplanas@suse.com>
:maturity:      new
:depends:       None
:platform:      Linux
'''
from __future__ import absolute_import, print_function, unicode_literals
import functools
import logging
import os.path
import tempfile
import traceback

log = logging.getLogger(__name__)

INSTALLATION_HELPER = '/usr/lib/snapper/installation-helper'
SNAPPER = '/usr/bin/snapper'

__virtualname__ = 'snapper_install'


# Define not exported variables from Salt, so this can be imported as
# a normal module
try:
    __grains__
    __opts__
    __pillars__
    __salt__
    __states__
    __utils__
except NameError:
    __grains__ = {}
    __opts__ = {}
    __pillars__ = {}
    __salt__ = {}
    __states__ = {}
    __utils__ = {}


def __virtual__():
    '''
    snapper_install requires the installation helper binary.

    '''
    if not os.path.exists(INSTALLATION_HELPER):
        return (False, '{} binary not found'.format(INSTALLATION_HELPER))
    return True


def _mount(device):
    '''
    Mount the device in a temporary place.
    '''
    dest = tempfile.mkdtemp()
    res = __salt__['mount.mount'](name=dest, device=device)
    if res is not True:
        log.error('Cannot mount device %s in %s', device, dest)
        _umount(dest)
        return None
    return dest


def _umount(path):
    '''
    Umount and clean the temporary place.
    '''
    __salt__['mount.umount'](path)
    __utils__['files.rm_rf'](path)


def __mount_device(action):
    '''
    Small decorator to makes sure that the mount and umount happends in
    a transactional way.
    '''
    @functools.wraps(action)
    def wrapper(*args, **kwargs):
        device = kwargs['device']

        ret = {
            'name': device,
            'result': False,
            'changes': {},
            'comment': ['Some error happends during the operation.'],
        }
        try:
            dest = _mount(device)
            if not dest:
                msg = 'Device {} cannot be mounted'.format(device)
                ret['comment'].append(msg)
            kwargs['__dest'] = dest
            ret = action(*args, **kwargs)
        except Exception as e:
            log.error('''Traceback: {}'''.format(traceback.format_exc()))
            ret['comment'].append(e)
        finally:
            _umount(dest)
        return ret
    return wrapper


def step_one(name, device, description):
    '''
    Step one of the installation-helper tool

    name
        Name of the state

    device
        Device where to install snapper

    description
        Description for the fist snapshot

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    # Mount the device and check if /etc/snapper/configs is present
    dest = _mount(device)
    if not dest:
        ret['comment'].append('Fail mounting {} in temporal directory {}'
                              .format(device, dest))
        return ret

    is_configs = os.path.exists(os.path.join(dest, 'etc/snapper/configs'))
    _umount(dest)

    if is_configs:
        ret['result'] = None if __opts__['test'] else True
        ret['comment'].append('Step one already applied to {}'.format(device))
        return ret

    if __opts__['test']:
        ret['comment'].append('Step one will be applied to {}'.format(device))
        return ret

    cmd = [INSTALLATION_HELPER, '--step', '1', '--device', device,
           '--description', description]
    res = __salt__['cmd.run_all'](cmd)

    if res['retcode'] or res['stderr']:
        ret['comment'].append('Failed to execute step one {}'
                              .format(res['stderr']))
    else:
        ret['result'] = True
        ret['changes']['step one'] = True
    return ret


@__mount_device
def step_two(name, device, prefix=None, __dest=None):
    '''
    Step two of the installation-helper tool

    name
       Name of the state

    device
        Device where to install snapper

    prefix
        Default root prefix for the subvolumes

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    snapshots = os.path.join(__dest, '.snapshots')
    if os.path.exists(snapshots):
        ret['result'] = None if __opts__['test'] else True
        ret['comment'].append('Step two aleady applied to {}'.format(device))
        return ret

    if __opts__['test']:
        ret['comment'].append('Step two will be applied to {}'.format(device))
        return ret

    cmd = [INSTALLATION_HELPER, '--step', '2', '--device', device,
           '--root-prefix', __dest]

    if prefix:
        cmd.extend(['--default-subvolume-name', prefix])

    res = __salt__['cmd.run_all'](cmd)

    if res['retcode'] or res['stderr']:
        ret['comment'].append('Failed to execute step two {}'
                              .format(res['stderr']))
    else:
        ret['result'] = True
        ret['changes']['step two'] = True

    # Internally step two mounts a new subvolume called .snapshots
    for i in range(5):
        res = __salt__['mount.umount'](snapshots)
        if res is not True:
            log.warning('Retry %s: Failed to umount %s: %s',
                        i, snapshots, res)
        else:
            break
    else:
        # We fail to umount .snapshots directory, bit the installation
        # step was properly executed, so we still return True
        ret['comment'].append('Failed to umount {}: {}'
                              .format(snapshots, res))

    return ret


def step_four(name, root):
    '''
    Step four of the installation-helper tool

    name
        Name of the state

    root
        Target directory where to chroot

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    if os.path.exists(os.path.join(root, '.snapshots/grub-snapshot.cfg')):
        ret['result'] = None if __opts__['test'] else True
        ret['comment'].append('Step four already applied to {}'.format(root))
        return ret

    if __opts__['test']:
        ret['comment'].append('Step four will be applied to {}'.format(root))
        return ret

    cmd = [INSTALLATION_HELPER, '--step', '4']
    res = __salt__['cmd.run_chroot'](root, cmd)

    if res['retcode'] or res['stderr']:
        ret['comment'].append('Failed to execute step four {}'
                              .format(res['stderr']))
        return ret

    # Set the initial configuration and quota as YaST is doing
    cmd = [SNAPPER, '--no-dbus', 'set-config', 'NUMBER_CLEANUP=yes',
           'NUMBER_LIMIT=2-10', 'NUMBER_LIMIT_IMPORTANT=4-10',
           'TIMELINE_CREATE=no']
    res = __salt__['cmd.run_chroot'](root, cmd)

    if res['retcode'] or res['stderr']:
        ret['comment'].append('Failed to set configuration in step four {}'
                              .format(res['stderr']))
        return ret

    cmd = [SNAPPER, '--no-dbus', 'setup-quota']
    res = __salt__['cmd.run_chroot'](root, cmd)

    if res['retcode'] or res['stderr']:
        ret['comment'].append('Failed to set quota in step four {}'
                              .format(res['stderr']))
        return ret

    ret['result'] = True
    ret['changes']['step four'] = True
    return ret


def step_five(name, root, snapshot_type, description, important, cleanup):
    '''
    Step five of the installation-helper tool

    name
        Name of the state

    root
        Target directory where to chroot

    snapshot_type
        Type of snapshot: {single, pre, post}

    description
        Description for the snapshot

    important
        Is the snapshot important

    cleanup
        Type or snapper cleanup angorithm: {number, timeline,
        empty-pre-post}

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    if snapshot_type not in ('single', 'pre', 'post'):
        ret['comment'].append('Value for snapshot_type not recognized')
        return ret

    if not description:
        ret['comment'].append('Value for description is empty')
        return ret

    if cleanup not in ('number', 'timeline', ' empty-pre-post '):
        ret['comment'].append('Value for cleanup not recognized')
        return ret

    cmd = [SNAPPER, '--no-dbus', 'list']
    res = __salt__['cmd.run_chroot'](root, cmd)

    if res['retcode'] or res['stderr']:
        ret['comment'].append('Failed to list snapshots in step five {}'
                              .format(res['stderr']))
        return ret

    if description in res['stdout']:
        ret['result'] = None if __opts__['test'] else True
        ret['comment'].append('Step five already applied to {}'.format(root))
        return ret

    if __opts__['test']:
        ret['comment'].append('Step five will be applied to {}'.format(root))
        return ret

    cmd = [INSTALLATION_HELPER, '--step', '5', '--snapshot-type',
           snapshot_type, '--description', '"{}"'.format(description),
           '--userdata', 'important={}'.format('yes' if important else
                                               'no'), '--cleanup', cleanup]
    res = __salt__['cmd.run_chroot'](root, cmd)

    if res['retcode'] or res['stderr']:
        ret['comment'].append('Failed to execute step five {}'
                              .format(res['stderr']))
    else:
        ret['result'] = True
        ret['changes']['step five'] = True
    return ret
