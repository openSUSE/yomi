# -*- coding: utf-8 -*-
#
# Author: Alberto Planas <aplanas@suse.com>
#
# Copyright 2019 SUSE LINUX GmbH, Nuernberg, Germany.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

'''
:maintainer:    Alberto Planas <aplanas@suse.com>
:maturity:      new
:depends:       None
:platform:      Linux
'''
from __future__ import absolute_import, print_function, unicode_literals
import logging


LOG = logging.getLogger(__name__)

__virtualname__ = 'devices'

__func_alias__ = {
    'filter_': 'filter',
}

# Define not exported variables from Salt, so this can be imported as
# a normal module
try:
    __grains__
    __salt__
except NameError:
    __grains__ = {}
    __salt__ = {}


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


def filter_(udev_in=None, udev_ex=None):
    '''
    Returns a list of devices, filtered under udev keys.

    udev_in
        A dictionary of key:values that are expected in the device
        udev information

    udev_ex
        A dictionary of key:values that are not expected in the device
        udev information (excluded)

    The key is a lower case string, joined by dots, that represent a
    path in the udev information dictionary. For example, 'e.id_bus'
    will represent the udev entry `udev['E']['ID_BUS']

    If the udev entry is a list, the algorithm will check that at
    least one item match one item of the value of the parameters.

    Returns list of devices that match `udev_in` and do not match
    `udev_ex`.

    CLI Example:

    .. code-block:: bash

       salt '*' devices.filter udev_in='{"e.id_bus": "ata"}'

    '''

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

    return sorted(devices_udev_key_in-devices_udev_key_ex)


def wipe(device):
    '''
    Remove all the partitions in the device.

    device
        Device name, for example /dev/sda

    Remove all the partitions, labels and flags from the device.

    CLI Example:

    .. code-block:: bash

       salt '*' devices.wipeout /dev/sda

    '''

    partitions = __salt__['partition.list'](device).get('partitions', [])
    for partition in partitions:
        # Remove filesystem information the the partition
        __salt__['disk.wipe']('{}{}'.format(device, partition))
        __salt__['partition.rm'](device, partition)

    # Remove the MBR information
    __salt__['disk.wipe']('{}'.format(device))
    __salt__['cmd.run']('dd bs=512 count=1 if=/dev/zero of={}'.format(device))

    return True


def _hwinfo_efi():
    '''Return information about EFI'''
    return {
        'efi': __grains__['efi'],
        'efi-secure-boot': __grains__['efi-secure-boot'],
    }


def _hwinfo_memory():
    '''Return information about the memory'''
    return {
        'mem_total': __grains__['mem_total'],
    }


def _hwinfo_network(short):
    '''Return network information'''
    info = {
        'fqdn': __grains__['fqdn'],
        'ip_interfaces':  __grains__['ip_interfaces'],
    }

    if not short:
        info['dns'] = __grains__['dns']

    return info


def hwinfo(items=None, short=True, listmd=False, devices=None):
    '''
    Probe for hardware

    items
        List of hardware items to inspect. Default ['bios', 'cpu', 'disk',
        'memory', 'network', 'partition']

    short
        Show only a summary. Default True.

    listmd
        Report RAID devices. Default False.

    devices
        List of devices to show information from. Default None.

    CLI Example:

    .. code-block:: bash

       salt '*' devices.hwinfo
       salt '*' devices.hwinfo items='["disk"]' short=no
       salt '*' devices.hwinfo items='["disk"]' short=no devices='["/dev/sda"]'
       salt '*' devices.hwinfo devices=/dev/sda

    '''
    result = {}

    if not items:
        items = ['bios', 'cpu', 'disk', 'memory', 'network', 'partition']
    if not isinstance(items, (list, tuple)):
        items = [items]

    if not devices:
        devices = []
    if devices and not isinstance(devices, (list, tuple)):
        devices = [devices]

    cmd = ['hwinfo']
    for item in items:
        cmd.append('--{}'.format(item))

    if short:
        cmd.append('--short')

    if listmd:
        cmd.append('--listmd')

    for device in devices:
        cmd.append('--only {}'.format(device))

    result['hwinfo'] = __salt__['cmd.run_stdout'](cmd)

    if 'bios' in items:
        result['bios grains'] = _hwinfo_efi()

    if 'memory' in items:
        result['memory grains'] = _hwinfo_memory()

    if 'network' in items:
        result['network grains'] = _hwinfo_network(short)

    return result
