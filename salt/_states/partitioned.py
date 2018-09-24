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

import salt.utils.path


LOG = logging.getLogger(__name__)

__virtualname__ = 'partitioned'


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


def __virtual__():
    '''
    Storage is only useful for images properly taylored.

    '''

    # TODO(aplanas) For now fail if the requirements are not meet.
    # Evaluate if makes sense to install the requirements inside the
    # state (parted, xfsprogs, btrfsprogs, lvm2)
    requirements = ('parted',)
    return all(salt.utils.path.which(req) for req in requirements)


def _check_label(device, label):
    '''
    Check if the label match with the device

    '''
    label = {
        'msdos': 'dos',
        }.get(label, label)
    res = __salt__['cmd.run'](['fdisk', '-l', device])
    return 'disklabel type: {}'.format(label) in res.lower()


def labeled(name, label):
    '''
    Make sure that the label of the partition is properly set.

    name
        Device name (/dev/sda, /dev/disk/by-id/scsi-...)

    label
        Label of the partition (usually 'gpd' or 'msdos')

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    if not label:
        ret['comment'].append('Label parameter is not optional')
        return ret

    if _check_label(name, label):
        ret['result'] = True
        ret['comment'].append('Label already set to {}'.format(label))
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'].append(
            'Label will be set to {} in {}'.format(label, name))
        ret['changes']['label'] = 'Will be set to {}'.format(label)
        return ret

    changes = __salt__['partition.mklabel'](name, label)

    if _check_label(name, label):
        ret['result'] = True
        ret['comment'].append('Label set to {} in {}'.format(label, name))
        ret['changes']['label'] = changes
    else:
        ret['comment'].append('Failed to set label to {}'.format(label))

    return ret


def _udev(udev_info, key):
    '''
    Return the value for a udev key.

    The `key` parameter is a lower case text joined by dots. For
    example, 'e.id_bus' will represent the key for
    `udev_info['E']['ID_BUS']`.

    '''
    k, _, r = key.partition('.')
    if not k:
        return udev_info
    if not isinstance(udev_info, dict):
        return 'n/a'
    if not r:
        return udev_info.get(k.upper(), 'n/a')
    return _udev(udev_info.get(k.upper(), {}), r)


def _match(udev_info, match_info):
    '''
    Check if `udev_info` match the information from `match_info`.
    '''
    res = True
    for key, value in match_info.items():
        udev_value = _udev(udev_info, key)
        if isinstance(udev_value, dict):
            # If is a dict we probably make a mistake in key from
            # match_info, as is not accessing a final value
            LOG.warning('The key %s for the udev information '
                        'dictionary is not a leaf element', key)
            continue

        # Converting both values to sets make easy to see if there is
        # a coincidence between both values
        value = set(value) if isinstance(value, list) else set([value])
        udev_value = set(udev_value) if isinstance(udev_value, list) \
            else set([udev_value])
        res = res and (value & udev_value)
    return res


def devices(name, udev_in=None, udev_ex=None):
    '''
    Returns a list of devices, filtered under udev keys.

    name
        Not used

    udev_key_in
        A dictionary of key: values that are expected in the device
        udev information

    udev_key_ex
        A dictionary of key: values that are not expected in the
        device udev information (excuded)

    The key is a lower case string, joined by dots, that represent a
    path in the udev information dictionary. For example, 's.id_bus'
    will represent the udev entry `udev['E']['ID_BUS']

    If the udev entry is a list, the algorithm will check that at
    least one item match one item of the value of the parameters.

    Returns in the `data` field a dictionary with two components:

      * `all_devices`: contains all the devices in the system
      * `devices`: list of filters that match `udev_key_in` and do not
        match `udev_key_ex`

    '''
    ret = {
        'name': name,
        'result': True,
        'changes': {},
        'comment': 'List of filtered devices',
        'data': {},
    }

    udev_in = udev_in if udev_in else {}
    udev_ex = udev_ex if udev_ex else {}

    all_devices = __grains__['disks']

    # Get the udev information only one time
    udev_info = {d: __salt__['udev.info'](d) for d in all_devices}

    devices_udev_key_in = {
        d for d in all_devices if _match(udev_info[d], udev_in)
    }
    devices_udev_key_ex = {
        d for d in all_devices if _match(udev_info[d], udev_ex) if udev_ex
    }

    ret['data'] = {
        'all_devices': all_devices,
        'devices': sorted(devices_udev_key_in-devices_udev_key_ex),
    }
    return ret
