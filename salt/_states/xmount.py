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
import logging

log = logging.getLogger(__name__)

__virtualname__ = 'fstab'


# Define not exported variables from Salt, so this can be imported as
# a normal module
try:
    __grains__
    __opts__
    __pillars__
    __salt__
    __states__
except NameError:
    __grains__ = {}
    __opts__ = {}
    __pillars__ = {}
    __salt__ = {}
    __states__ = {}


def _convert_to(maybe_device, convert_to):
    '''
    Convert a device name, UUID or LABEL to a devide name, UUID or
    LABEL.

    Return the fs_spec required for fstab.

    '''

    # Fast path. If we already have the information required, we can
    # save one blkid call
    if not convert_to or \
       (convert_to == 'device' and maybe_device.startswith('/')) or \
       maybe_device.startswith('{}='.format(convert_to.upper())):
        return maybe_device

    # Get the device information
    if maybe_device.startswith('/'):
        blkid = __salt__['disk.blkid'](maybe_device)
    else:
        blkid = __salt__['disk.blkid'](token=maybe_device)

    result = None
    if len(blkid) == 1:
        if convert_to == 'device':
            result = list(blkid.keys())[0]
        else:
            key = convert_to.upper()
            result = '{}={}'.format(key, list(blkid.values())[0][key])

    return result


def fstab_present(name, fs_file, fs_vfstype, fs_mntops='defaults',
                  fs_freq=0, fs_passno=0, mount_by=None,
                  config='/etc/fstab', mount=True, match_on='auto'):
    '''
    Makes sure that a fstab mount point is pressent.

    name
        The name of block device. Can be any valid fs_spec value.

    fs_file
        Mount point (target) for the filesystem.

    fs_vfstype
        The type of the filesystem (e.g. ext4, xfs, btrfs, ...)

    fs_mntops
        The mount options associated with the filesystem. Default is
        ``defaults``.

    fs_freq
        Field is used by dump to determine which fs need to be
        dumped. Default is ``0``

    fs_passno
        Field is used by fsck to determine the order in which
        filesystem checks are done at boot time. Default is ``0``

    mount_by
        Select the final value for fs_spec. Can be [``None``,
        ``device``, ``label``, ``uuid``, ``partlabel``,
        ``partuuid``]. If ``None``, the value for fs_spect will be the
        parameter ``name``, in other case will search the correct
        value based on the device name. For example, for ``uuid``, the
        value for fs_spec will be of type 'UUID=xxx' instead of the
        device name set in ``name``.

    config
        Place where the fstab file lives. Default is ``/etc/fstab``

    mount
        Set if the mount should be mounted immediately. Default is
        ``True``

    match_on
        A name or list of fstab properties on which this state should
        be applied.  Default is ``auto``, a special value indicating
        to guess based on fstype.  In general, ``auto`` matches on
        name for recognized special devices and device otherwise.

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    # Adjust fs_mntops based on the OS
    if fs_mntops == 'defaults':
        if __grains__['os'] in ['MacOS', 'Darwin']:
            fs_mntops = 'noowners'
        elif __grains__['os'] == 'AIX':
            fs_mntops = ''

    # Adjust the config file based on the OS
    if config == '/etc/fstab':
        if __grains__['os'] in ['MacOS', 'Darwin']:
            config = '/etc/auto_salt'
        elif __grains__['os'] == 'AIX':
            config = '/etc/filesystems'

    if not fs_file == '/':
        fs_file = fs_file.rstrip('/')

    fs_spec = _convert_to(name, mount_by)

    # Validate that the device is valid after the conversion
    if not fs_spec:
        msg = 'Device {} cannot be converted to {}'
        ret['comment'].append(msg.format(name, mount_by))
        return ret

    if __opts__['test']:
        if __grains__['os'] in ['MacOS', 'Darwin']:
            out = __salt__['mount.set_automaster'](name=fs_file,
                                                   device=fs_spec,
                                                   fstype=fs_vfstype,
                                                   opts=fs_mntops,
                                                   config=config,
                                                   test=True)
        elif __grains__['os'] == 'AIX':
            out = __salt__['mount.set_filesystems'](name=fs_file,
                                                    device=fs_spec,
                                                    fstype=fs_vfstype,
                                                    opts=fs_mntops,
                                                    mount=mount,
                                                    config=config,
                                                    test=True,
                                                    match_on=match_on)
        else:
            out = __salt__['mount.set_fstab'](name=fs_file,
                                              device=fs_spec,
                                              fstype=fs_vfstype,
                                              opts=fs_mntops,
                                              dump=fs_freq,
                                              pass_num=fs_passno,
                                              config=config,
                                              test=True,
                                              match_on=match_on)
        ret['result'] = None
        if out == 'present':
            msg = '{} entry is already in {}.'
            ret['comment'].append(msg.format(fs_file, config))
        elif out == 'new':
            msg = '{} entry will be written in {}.'
            ret['comment'].append(msg.format(fs_file, config))
        elif out == 'change':
            msg = '{} entry will be updated in {}.'
            ret['comment'].append(msg.format(fs_file, config))
        else:
            ret['result'] = False
            msg = '{} entry cannot be created in {}: {}.'
            ret['comment'].append(msg.format(fs_file, config, out))
        return ret

    if __grains__['os'] in ['MacOS', 'Darwin']:
        out = __salt__['mount.set_automaster'](name=fs_file,
                                               device=fs_spec,
                                               fstype=fs_vfstype,
                                               opts=fs_mntops,
                                               config=config)
    elif __grains__['os'] == 'AIX':
        out = __salt__['mount.set_filesystems'](name=fs_file,
                                                device=fs_spec,
                                                fstype=fs_vfstype,
                                                opts=fs_mntops,
                                                mount=mount,
                                                config=config,
                                                match_on=match_on)
    else:
        out = __salt__['mount.set_fstab'](name=fs_file,
                                          device=fs_spec,
                                          fstype=fs_vfstype,
                                          opts=fs_mntops,
                                          dump=fs_freq,
                                          pass_num=fs_passno,
                                          config=config,
                                          match_on=match_on)

    ret['result'] = True
    if out == 'present':
        msg = '{} entry was already in {}.'
        ret['comment'].append(msg.format(fs_file, config))
    elif out == 'new':
        ret['changes']['persist'] = 'new'
        msg = '{} entry added in {}.'
        ret['comment'].append(msg.format(fs_file, config))
    elif out == 'change':
        msg = '{} entry updated in {}.'
        ret['comment'].append(msg.format(fs_file, config))
    else:
        ret['result'] = False
        msg = '{} entry cannot be changed in {}: {}.'
        ret['comment'].append(msg.format(fs_file, config, out))

    return ret


def fstab_absent(name, fs_file, config='/etc/fstab'):
    '''
    Makes sure that a fstab mount point is absent.

    name
        The name of block device. Can be any valid fs_spec value.

    fs_file
        Mount point (target) for the filesystem.

    config
        Place where the fstab file lives

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    # Adjust the config file based on the OS
    if config == '/etc/fstab':
        if __grains__['os'] in ['MacOS', 'Darwin']:
            config = '/etc/auto_salt'
        elif __grains__['os'] == 'AIX':
            config = '/etc/filesystems'

    if not fs_file == '/':
        fs_file = fs_file.rstrip('/')

    if __opts__['test']:
        if __grains__['os'] in ['MacOS', 'Darwin']:
            fstab_data = __salt__['mount.automaster'](config)
        elif __grains__['os'] == 'AIX':
            fstab_data = __salt__['mount.filesystems'](config)
        else:
            fstab_data = __salt__['mount.fstab'](config)

        ret['result'] = None
        if fs_file not in fstab_data:
            msg = '{} entry is already missing in {}.'
            ret['comment'].append(msg.format(fs_file, config))
        else:
            msg = '{} entry will be removed from {}.'
            ret['comment'].append(msg.format(fs_file, config))
        return ret

    if __grains__['os'] in ['MacOS', 'Darwin']:
        out = __salt__['mount.rm_automaster'](name=fs_file,
                                              device=name,
                                              config=config)
    elif __grains__['os'] == 'AIX':
        out = __salt__['mount.rm_filesystems'](name=fs_file,
                                               device=name,
                                               config=config)
    else:
        out = __salt__['mount.rm_fstab'](name=fs_file,
                                         device=name,
                                         config=config)

    if out is not True:
        ret['result'] = False
        msg = '{} entry failed when removing from {}.'
        ret['comment'].append(msg.format(fs_file, config))
    else:
        ret['result'] = True
        ret['changes']['persist'] = 'removed'
        msg = '{} entry removed from {}.'
        ret['comment'].append(msg.format(fs_file, config))

    return ret
