# Copyright (c) 2018 SUSE LINUX GmbH, Nuernberg, Germany.

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

from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

__virtualname__ = 'btrfs'


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


def _mount(device):
    '''
    Mount the device in a temporary place.
    '''
    dest = tempfile.mkdtemp()
    res = __states__['mount.mounted'](dest, device=device, fstype='btrfs',
                                      opts='subvol=/', persist=False)
    if not res['result']:
        log.error('Cannot mount device %s in %s', device, dest)
        _umount(dest)
        return None
    return dest


def _umount(path):
    '''
    Umount and clean the temporary place.
    '''
    __states__['mount.unmounted'](path)
    __utils__['files.rm_rf'](path)


def _is_default(path, dest, name):
    '''
    Check if the subvolume is the current default.
    '''
    subvol_id = __salt__['btrfs.subvolume_show'](path)[name]['subvolume id']
    def_id = __salt__['btrfs.subvolume_get_default'](dest)['id']
    return subvol_id == def_id


def _set_default(path, dest, name):
    '''
    Set the subvolume as the current default.
    '''
    subvol_id = __salt__['btrfs.subvolume_show'](path)[name]['subvolume id']
    return __salt__['btrfs.subvolume_set_default'](subvol_id, dest)


def _is_cow(path):
    '''
    Check if the subvolume is copy on write
    '''
    dirname = os.path.dirname(path)
    return 'C' not in __salt__['file.lsattr'](dirname)[path]


def _unset_cow(path):
    '''
    Disable the copy on write in a subvolume
    '''
    return __salt__['file.chattr'](path, operator='add', attributes='C')


def __mount_device(action):
    '''
    Small decorator to makes sure that the mount and umount happends in
    a transactional way.
    '''
    @functools.wraps(action)
    def wrapper(*args, **kwargs):
        name = kwargs['name']
        device = kwargs['device']

        ret = {
            'name': name,
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


@__mount_device
def subvolume_created(name, device, qgroupids=None, set_default=False,
                      copy_on_write=True, __dest=None):
    '''
    Makes sure that a btrfs subvolume is present.

    name
        Name of the subvolume to add

    device
        Device where to create the subvolume

    qgroupids
         Add the newly created subcolume to a qgroup. This parameter
         is a list

    set_default
        If True, this new subvolume will be set as default when
        mounted, unless subvol option in mount is used

    copy_on_write
        If false, set the subvolume with chattr +C

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }
    path = os.path.join(__dest, name)

    exists = __salt__['btrfs.subvolume_exists'](path)
    if exists:
        ret['comment'].append('Subvolume {} already present'.format(name))

    # Resolve first the test case. The check is not complete, but at
    # least we will report if a subvolume needs to be created. Can
    # happend that the subvolume is there, but we also need to set it
    # as default, or persist in fstab.
    if __opts__['test']:
        ret['result'] = None
        if not exists:
            ret['comment'].append('Subvolume {} will be created'.format(name))
        return ret

    if not exists:
        # Create the directories where the subvolume lives
        _path = os.path.dirname(path)
        res = __states__['file.directory'](_path, makedirs=True)
        if not res['result']:
            ret['comment'].append('Error creating {} directory'.format(_path))
            return ret

        try:
            __salt__['btrfs.subvolume_create'](name, dest=__dest,
                                               qgroupids=qgroupids)
        except CommandExecutionError:
            ret['comment'].append('Error creating subvolume {}'.format(name))
            return ret

        ret['changes'][name] = 'Created subvolume {}'.format(name)

    if set_default and not _is_default(path, __dest, name):
        ret['changes'][name + '_default'] = _set_default(path, __dest, name)

    if not copy_on_write and _is_cow(path):
        ret['changes'][name + '_cow'] = _unset_cow(path)

    ret['result'] = True
    return ret


@__mount_device
def subvolume_deleted(name, device, commit=False, __dest=None):
    '''
    Makes sure that a btrfs subvolume is removed.

    name
        Name of the subvolume to remove

    device
        Device where to remove the subvolume

    commit
        Wait until the transaction is over

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    path = os.path.join(__dest, name)

    exists = __salt__['btrfs.subvolume_exists'](path)
    if not exists:
        ret['comment'].append('Subvolume {} already missing'.format(name))

    if __opts__['test']:
        ret['result'] = None
        if exists:
            ret['comment'].append('Subvolume {} will be removed'.format(name))
        return ret

    # If commit is set, we wait until all is over
    commit = 'after' if commit else None

    if not exists:
        try:
            __salt__['btrfs.subvolume_delete'](path, commit=commit)
        except CommandExecutionError:
            ret['comment'].append('Error removing subvolume {}'.format(name))
            return ret

        ret['changes'][name] = 'Removed subvolume {}'.format(name)

    ret['result'] = True
    return ret