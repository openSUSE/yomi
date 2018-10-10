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
import re

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


class ParseException(Exception):
    pass


class EnumerateException(Exception):
    pass


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
        Label of the partition (usually 'gpt' or 'msdos')

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


def _get_partition_type(device):
    '''
    Get partition type of each partition

    Return a list of tuples: [(number, type), ...]

    '''
    cmd = 'parted -s {0} print'.format(device)
    out = __salt__['cmd.run_stdout'](cmd)
    return re.findall(r'\s*(\d+).*(primary|extended|logical).*', out)


def _get_cached_info(device):
    '''
    Get the information of a device as a dictionary

    '''
    if not hasattr(_get_cached_info, 'info'):
        _get_cached_info.info = __salt__['partition.list'](device)['info']
    return _get_cached_partitions.info


def _get_cached_partitions(device, unit='s'):
    '''
    Get the partitions as a dictionary

    '''
    # `partitions` will be used as a local cache, to avoid multiple
    # request of the same partition with the same units. Is a
    # dictionary where the key is the `unit`, as we will make request
    # of all partitions under this unit. This potentially can low the
    # complexity algorithm to amortized O(1).
    if not hasattr(_get_cached_partitions, 'partitions'):
        _get_cached_partitions.partitions = {}
        # There is a bug in `partition.list`, where `type` is storing
        # the file system information, to workaround this we get the
        # partition type using parted and attach it here.
        _get_cached_partitions.types = _get_partition_type(device)
    partitions = _get_cached_partitions.partitions

    if unit not in partitions:
        partitions[unit] = __salt__['partition.list'](device, unit=unit)
        # We manually add the types in the partition information
        for number, type_ in _get_cached_partitions.types:
            partitions[unit]['partitions'][number]['type'] = type_

    return partitions[unit]['partitions']


def _parse_value_with_units(value, default='MB'):
    '''
    Split a value with (optionally) is expressed in units.

    Returns the tuple (value, unit)
    '''
    valid_units = ('s', 'B', 'kB', 'MB', 'MiB', 'GB', 'GiB', 'TB',
                   'TiB', '%', 'cyl', 'chs', 'compact')
    match = re.search(r'^([\d.]+)(\D*)$', str(value))
    if match:
        value, unit = match.groups()
        unit = unit if unit else default
        if unit in valid_units:
            return (str(value), unit)
    raise ParseException('{} not recognized as a valid unit'.format(value))


def _check_partition(device, number, part_type, start, end):
    '''
    Check if the proposed partition match the current one.

    Returns a tri-state value:
      - `True`: the proposed partition match
      - `False`: the proposed partition do not match
      - `None`: the proposed partition is a new partition
    '''
    # The `start` and `end` fields are expressed with units (the same
    # kind of units that `parted` allows). To make a fair comparison
    # we need to normalize each field to the same units that we can
    # use to read the current partitions. A good candidate is sector
    # ('s'). The problem is that we need to reimplement the same
    # conversion logic from `parted` here [1], as we need the same
    # round logic when we covert from 'MiB' to 's', for example.
    #
    # To avoid this duplicity of code we can do a trick: for each
    # field in the proposed partition we request a `partition.list`
    # with the same unit. We make `parted` to make the conversion for
    # us, in exchange for an slower algorithm.
    #
    # We can change it once we decide to take care of alignment.
    #
    # [1] Check libparted/unit.c

    number = str(number)
    partitions = _get_cached_partitions(device)
    if number not in partitions:
        return None

    if part_type != partitions[number]['type']:
        return False

    for value, name in ((start, 'start'), (end, 'end')):
        value, unit = _parse_value_with_units(value)
        current_value = _get_cached_partitions(device, unit)[number][name]
        current_value, _ = _parse_value_with_units(current_value)
        if value != current_value:
            return False

    return True


def _get_first_overlapping_partition(device, start):
    '''
    Return the partition that contains the start point.

    '''
    # Check if there is a partition in the system that start at
    # specified point.
    value, unit = _parse_value_with_units(start)
    value = int(value)
    partitions = _get_cached_partitions(device, unit)
    partition_number = None
    partition_start = 0
    for number, partition in partitions.items():
        p_start = int(_parse_value_with_units(partition['start'])[0])
        p_end = int(_parse_value_with_units(partition['end'])[0])
        if p_start <= value and p_end >= value:
            if not partition_number or partition_start >= value:
                partition_number = number
                partition_start = value
    return partition_number


def _get_partition_number(device, part_type, start, end):
    '''
    Return a partition number for a [start, end] range and a partition
    type.

    If the range is allocated and the partition type match, return the
    partition number. If the type do not match but is a logical
    partition inside an extended one, return the next partition
    number.

    If the range is not allocated, return the next partition number.

    '''

    unit = _parse_value_with_units(start)[1]
    partitions = _get_cached_partitions(device, unit)

    # Check if there is a partition in the system that start at
    # specified point and match the same type.
    number = _get_first_overlapping_partition(device, start)
    if number:
        if partitions[number]['type'] == part_type:
            return number
        elif not (partitions[number]['type'] == 'extended'
                  and part_type == 'logical'):
            raise EnumerateException('Do not overlap partitions')

    def __primary_partition_free_slot(partitions, label):
        if label == 'msdos':
            max_primary = 4
        else:
            max_primary = 1024
        for i in range(1, max_primary + 1):
            i = str(i)
            if i not in partitions:
                return i

    # The partition is not already there, we guess the next number
    label = _get_cached_info(device)['partition table']
    if part_type == 'primary':
        candidate = __primary_partition_free_slot(partitions, label)
        if not candidate:
            raise EnumerateException('No free slot for primary partition')
        return candidate
    elif part_type == 'extended':
        if label == 'gpt':
            raise EnumerateException('Extended partitions not allowed in gpt')
        if 'extended' in (info['type'] for info in partitions.values()):
            raise EnumerateException('Already found a extended partition')
        candidate = __primary_partition_free_slot(partitions, label)
        if not candidate:
            raise EnumerateException('No free slot for extended partition')
        return candidate
    elif part_type == 'logical':
        if label == 'gpt':
            raise EnumerateException('Extended partitions not allowed in gpt')
        if 'extended' not in (part['type'] for part in partitions.values()):
            raise EnumerateException('Missing extended partition')
        candidate = max((int(part['number'])
                         for part in partitions.values()
                         if part['type'] == 'logical'), default=4)
        return str(candidate + 1)


def mkparted(name, part_type, fs_type=None, start=None, end=None):
    '''
    Make sure that a partition is allocated in the disk.

    name
        Device or partition name. If the name is like /dev/sda, parted
        will take care of creating the partition on the next slot. If
        the name is like /dev/sda1, we will consider partition 1 as a
        reference for the match.

    part_type
        Type of partition, should be one of "primary", "logical", or
        "extended".

    fs_type
        Expected filesystem, following the parted names.

    start
        Start of the partition (in parted units)

    end
        End of the partition (in parted units)

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    if part_type not in ('primary', 'extended', 'logical'):
        ret['comment'].append('Partition type not recognized')
    if not start or not end:
        ret['comment'].append('Parameters start and end are not optional')

    # If the user do not provide any partition number we get generate
    # the next available for the partition type
    device, number = re.search(r'(\D+)(\d*)', name).groups()
    if not number:
        try:
            number = _get_partition_number(device, part_type, start, end)
        except EnumerateException as e:
            ret['comment'].appent(str(e))

    # If at this point we have some comments, we return with a fail
    if ret['comment']:
        return ret

    # Check if the partition is already there or we need to create a
    # new one
    partition_match = _check_partition(name, device, number,
                                       part_type, fs_type, start, end)

    if partition_match:
        ret['comment'].append('Partition {}{} already '
                              'in place'.format(device, number))
    elif partition_match is None:
        ret['changes']['new'] = 'Partition {}{} will ' \
            'be created'.format(device, number)
    elif partition_match is False:
        ret['comment'].append('Partition {}{} cannot '
                              'be replaced'.format(device, number))

    if __opts__['test']:
        ret['result'] = None
        return ret

    if partition_match is False:
        # TODO(aplanas) with parted we cannot force a partition number
        res = __salt__['partition.mkpart'](device, part_type, fs_type,
                                           start, end)
        ret['changed']['output'] = res

    partition_match = _check_partition(name, device, number,
                                       part_type, fs_type, start, end)
    if partition_match:
        ret['result'] = True
    elif not partition_match:
        ret['commend'].append('Partition {}{} fail to '
                              'be created'.format(device, number))
        ret['result'] = False

    return ret


def _check_partition_name(device, partition, name):
    '''
    Check if the partition have this name.
    '''
    pass


def named(name, device, partition=None):
    '''
    Make sure that a gpt partition have set a name.

    name
        Name or label for the partition

    device
        Device name (/dev/sda, /dev/disk/by-id/scsi-...) or partition

    partition
        Partition number (can be in the device)

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    if not partition:
        device, partition = re.search(r'(\D+)(\d*)', name).groups()
    if not partition:
        ret['comment'].append('Partition number not provided')

    if not _check_label(device, 'gpt'):
        ret['comment'].append('Only gpt partitions can be named')

    if _check_partition_name(device, partition, name):
        ret['result'] = True
        ret['comment'].append('Name of the partition {}{} is '
                              'already "{}"'.format(device, partition, name))

    if ret['comment']:
        return ret

    if __opts__['test']:
        ret['comment'].append('Partition {}{} will be named '
                              '"{}"'.format(device, partition, name))
        ret['changes']['name'] = 'Name will be set to {}'.format(name)
        return ret

    changes = __salt__['partition.name'](device, partition, name)

    if _check_partition_name(device, partition, name):
        ret['result'] = True
        ret['comment'].append('Name set to {} in {}{}'.format(name, device,
                                                              partition))
        ret['changes']['name'] = changes
    else:
        ret['comment'].append('Failed to set name to {}'.format(name))

    return ret
