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

import unittest
from unittest.mock import patch

from states import partitioned


class PartitionedTestCase(unittest.TestCase):

    @patch('states.partitioned.__salt__')
    def test_check_label(self, __salt__):
        __salt__.__getitem__.return_value = lambda _: 'Disklabel type: dos'
        self.assertTrue(partitioned._check_label('/dev/sda', 'msdos'))
        self.assertTrue(partitioned._check_label('/dev/sda', 'dos'))
        self.assertFalse(partitioned._check_label('/dev/sda', 'gpt'))

        __salt__.__getitem__.return_value = lambda _: ''
        self.assertFalse(partitioned._check_label('/dev/sda', 'msdos'))
        self.assertFalse(partitioned._check_label('/dev/sda', 'gpt'))

    @patch('states.partitioned.__opts__')
    @patch('states.partitioned.__salt__')
    def test_labeled(self, __salt__, __opts__):
        __opts__.__getitem__.return_value = False

        __salt__.__getitem__.return_value = lambda _: 'Disklabel type: dos'
        self.assertEqual(
            partitioned.labeled('/dev/sda', 'msdos'),
            {
                'name': '/dev/sda',
                'result': True,
                'changes': {},
                'comment': ['Label already set to msdos'],
            }
        )

        __salt__.__getitem__.side_effect = (
            lambda _: '',
            lambda _a, _b: True,
            lambda _: 'Disklabel type: dos',
        )
        self.assertEqual(
            partitioned.labeled('/dev/sda', 'msdos'),
            {
                'name': '/dev/sda',
                'result': True,
                'changes': {
                    'label': 'Label set to msdos in /dev/sda',
                },
                'comment': ['Label set to msdos in /dev/sda'],
            }
        )

    def test_udev(self):
        self.assertEqual(partitioned._udev({'A': {'B': 1}}, 'a.b'), 1)
        self.assertEqual(partitioned._udev({'A': {'B': 1}}, 'A.B'), 1)
        self.assertEqual(partitioned._udev({'A': {'B': 1}}, 'a.c'), 'n/a')
        self.assertEqual(partitioned._udev({'A': [1, 2]}, 'a.b'), 'n/a')
        self.assertEqual(partitioned._udev({'A': {'B': 1}}, ''),
                         {'A': {'B': 1}})

    def test_match(self):
        self.assertTrue(partitioned._match({'A': {'B': 1}}, {'a.b': 1}))
        self.assertFalse(partitioned._match({'A': {'B': 1}}, {'a.b': 2}))
        self.assertTrue(partitioned._match({'A': {'B': 1}}, {'a.b': [1, 2]}))
        self.assertFalse(partitioned._match({'A': {'B': 1}}, {'a.b': [2, 3]}))
        self.assertTrue(partitioned._match({'A': {'B': [1, 2]}}, {'a.b': 1}))
        self.assertTrue(partitioned._match({'A': {'B': [1, 2]}},
                                           {'a.b': [1, 3]}))
        self.assertFalse(partitioned._match({'A': {'B': [1, 2]}},
                                            {'a.b': [3, 4]}))
        self.assertTrue(partitioned._match({'A': 1}, {}))

    @patch('states.partitioned.__grains__')
    @patch('states.partitioned.__salt__')
    def test_devices(self, __salt__, __grains__):
        cdrom = {
            'S': ['dvd', 'cdrom'],
            'E': {'ID_BUS': 'ata'},
        }
        usb = {
            'E': {'ID_BUS': 'usb'},
        }
        hd = {
            'E': {'ID_BUS': 'ata'},
        }

        __grains__.__getitem__.return_value = ['sda', 'sdb', 'sr0']
        __salt__.__getitem__.return_value = lambda d: {
            'sda': hd, 'sdb': usb, 'sr0': cdrom
        }[d]

        self.assertEqual(
            partitioned.devices('only ata', {'e.id_bus': 'ata'}, {}),
            {
                'name': 'only ata',
                'result': True,
                'changes': {},
                'comment': 'List of filtered devices',
                'data': {
                    'all_devices': ['sda', 'sdb', 'sr0'],
                    'devices': ['sda', 'sr0'],
                }
            }
        )
        self.assertEqual(
            partitioned.devices('only usb', {'e.id_bus': 'usb'}, {}),
            {
                'name': 'only usb',
                'result': True,
                'changes': {},
                'comment': 'List of filtered devices',
                'data': {
                    'all_devices': ['sda', 'sdb', 'sr0'],
                    'devices': ['sdb'],
                }
            }
        )
        self.assertEqual(
            partitioned.devices('only installable media', {'e.id_bus': 'ata'},
                                {'s': ['cdrom']}),
            {
                'name': 'only installable media',
                'result': True,
                'changes': {},
                'comment': 'List of filtered devices',
                'data': {
                    'all_devices': ['sda', 'sdb', 'sr0'],
                    'devices': ['sda'],
                }
            }
        )

    @patch('states.partitioned.__salt__')
    def test_get_partition_type(self, __salt__):
        __salt__.__getitem__.return_value = lambda _: """
Model: ATA ST2000DM001-9YN1 (scsi)
Disk /dev/sda: 2000GB
Sector size (logical/physical): 512B/4096B
Partition Table: msdos
Disk Flags:

Number  Start   End     Size    Type     File system     Flags
 1      1049kB  2155MB  2154MB  primary  linux-swap(v1)  type=82
 2      2155MB  45.1GB  43.0GB  primary  btrfs           boot, type=83
 3      45.1GB  2000GB  1955GB  primary  xfs             type=83
        """
        self.assertEqual(
            partitioned._get_partition_type('/dev/sda'),
            [('1', 'primary'), ('2', 'primary'), ('3', 'primary')]
        )

        __salt__.__getitem__.return_value = lambda _: """
Model: ATA QEMU HARDDISK (scsi)
Disk /dev/sda: 25.8GB
Sector size (logical/physical): 512B/512B
Partition Table: msdos
Disk Flags:

Number  Start   End     Size    Type      File system  Flags
 1      1049kB  11.5MB  10.5MB  extended               type=05
 5      2097kB  5243kB  3146kB  logical                type=83
 3      11.5GB  22.0MB  10.5MB  primary                type=83
        """
        self.assertEqual(
            partitioned._get_partition_type('/dev/sda'),
            [('1', 'extended'), ('5', 'logical'), ('3', 'primary')]
        )

    @patch('states.partitioned.__salt__')
    def test_get_cached_partitions(self, __salt__):
        __salt__.__getitem__.side_effect = [
            lambda _: '1 primary',
            lambda _, unit: {
                'info': None,
                'partitions': {'1': {}},
            },
        ]

        self.assertEqual(
            partitioned._get_cached_partitions('/dev/sda', 's'),
            {'1': {'type': 'primary'}}
        )

    def test_parse_value_with_units(self):
        self.assertEqual(partitioned._parse_value_with_units(1), (1, 'MB'))
        self.assertEqual(partitioned._parse_value_with_units('1'), (1, 'MB'))
        self.assertEqual(partitioned._parse_value_with_units('1.0'), (1, 'MB'))
        self.assertEqual(partitioned._parse_value_with_units('1s'), (1, 's'))
        self.assertEqual(partitioned._parse_value_with_units('1.1s'),
                         (1.1, 's'))
        self.assertRaises(partitioned.ParseException,
                          partitioned._parse_value_with_units, 's1')

    @patch('states.partitioned._get_cached_partitions')
    def test_check_partition(self, _get_cached_partitions):
        _get_cached_partitions.return_value = {
            '1': {
                'type': 'primary',
                'size': '10s',
                'start': '0s',
                'end': '10s',
            }
        }
        self.assertTrue(partitioned._check_partition('/dev/sda', 1, 'primary',
                                                     '0s', '10s'))
        self.assertTrue(partitioned._check_partition('/dev/sda', '1',
                                                     'primary', '0s', '10s'))
        self.assertFalse(partitioned._check_partition('/dev/sda', '1',
                                                      'primary', '10s', '20s'))
        self.assertEqual(partitioned._check_partition('/dev/sda', '2',
                                                      'primary', '10s', '20s'),
                         None)

        _get_cached_partitions.return_value = {
            '1': {
                'type': 'primary',
                'size': '100kB',
                'start': '0.5kB',
                'end': '100kB',
            }
        }
        self.assertTrue(partitioned._check_partition('/dev/sda', '1',
                                                     'primary', '0kB',
                                                     '100kB'))
        self.assertTrue(partitioned._check_partition('/dev/sda', '1',
                                                     'primary', '1kB',
                                                     '100kB'))
        self.assertFalse(partitioned._check_partition('/dev/sda', '1',
                                                      'primary', '1.5kB',
                                                      '100kB'))

    @patch('states.partitioned._get_cached_partitions')
    def test_get_first_overlapping_partition(self, _get_cached_partitions):
        _get_cached_partitions.return_value = {}
        self.assertEqual(
            partitioned._get_first_overlapping_partition('/dev/sda',
                                                         '0s'), None)

        _get_cached_partitions.return_value = {
            '1': {
                'number': '1',
                'type': 'primary',
                'size': '10s',
                'start': '0s',
                'end': '10s',
            }
        }
        self.assertEqual(
            partitioned._get_first_overlapping_partition('/dev/sda',
                                                         '0s'), '1')

        _get_cached_partitions.return_value = {
            '1': {
                'number': '1',
                'type': 'primary',
                'size': '100kB',
                'start': '0.51kB',
                'end': '100kB',
            }
        }
        self.assertEqual(
            partitioned._get_first_overlapping_partition('/dev/sda',
                                                         '0kB'), '1')

        _get_cached_partitions.return_value = {
            '1': {
                'number': '1',
                'type': 'extended',
                'size': '10s',
                'start': '0s',
                'end': '10s',
            },
            '5': {
                'number': '5',
                'type': 'logical',
                'size': '4s',
                'start': '1s',
                'end': '5s',
            }
        }
        self.assertEqual(
            partitioned._get_first_overlapping_partition('/dev/sda',
                                                         '0s'), '1')

        self.assertEqual(
            partitioned._get_first_overlapping_partition('/dev/sda',
                                                         '1s'), '5')

    @patch('states.partitioned._get_cached_info')
    @patch('states.partitioned._get_cached_partitions')
    def test_get_partition_number_primary(self, _get_cached_partitions,
                                          _get_cached_info):
        _get_cached_info.return_value = {'partition table': 'msdos'}
        _get_cached_partitions.return_value = {}

        partition_data = ('/dev/sda', 'primary', '0s', '10s')
        self.assertEqual(
            partitioned._get_partition_number(*partition_data), '1')

        _get_cached_partitions.return_value = {
            '1': {
                'number': '1',
                'type': 'primary',
                'size': '10s',
                'start': '0s',
                'end': '10s',
            }
        }
        self.assertEqual(
            partitioned._get_partition_number(*partition_data), '1')

        partition_data = ('/dev/sda', 'primary', '0s', '10s')
        self.assertEqual(
            partitioned._get_partition_number(*partition_data), '1')

        _get_cached_partitions.return_value = {
            '1': {
                'number': '1',
                'type': 'primary',
                'start': '0s',
                'end': '10s',
            },
            '2': {
                'number': '2',
                'type': 'primary',
                'start': '11s',
                'end': '20s',
            },
            '3': {
                'number': '3',
                'type': 'primary',
                'start': '21s',
                'end': '30s',
            },
            '4': {
                'number': '4',
                'type': 'primary',
                'start': '31s',
                'end': '40s',
            },
        }

        partition_data = ('/dev/sda', 'primary', '41s', '50s')
        self.assertRaises(partitioned.EnumerateException,
                          partitioned._get_partition_number,
                          *partition_data)

        _get_cached_info.return_value = {'partition table': 'gpt'}
        partition_data = ('/dev/sda', 'primary', '41s', '50s')
        self.assertEqual(
            partitioned._get_partition_number(*partition_data), '5')

    @patch('states.partitioned._get_cached_info')
    @patch('states.partitioned._get_cached_partitions')
    def test_get_partition_number_extended(self, _get_cached_partitions,
                                           _get_cached_info):
        _get_cached_info.return_value = {'partition table': 'msdos'}
        _get_cached_partitions.return_value = {}
        partition_data = ('/dev/sda', 'extended', '0s', '10s')
        self.assertEqual(
            partitioned._get_partition_number(*partition_data), '1')

        _get_cached_partitions.return_value = {
            '1': {
                'number': '1',
                'type': 'primary',
                'start': '0s',
                'end': '10s',
            },
        }
        partition_data = ('/dev/sda', 'extended', '21s', '30s')
        self.assertEqual(
            partitioned._get_partition_number(*partition_data), '2')

        _get_cached_partitions.return_value = {
            '1': {
                'number': '1',
                'type': 'primary',
                'start': '0s',
                'end': '10s',
            },
            '2': {
                'number': '2',
                'type': 'extended',
                'start': '11s',
                'end': '20s',
            },
        }
        self.assertRaises(partitioned.EnumerateException,
                          partitioned._get_partition_number,
                          *partition_data)

        _get_cached_partitions.return_value = {
            '1': {
                'number': '1',
                'type': 'primary',
                'start': '0s',
                'end': '10s',
            },
            '2': {
                'number': '2',
                'type': 'primary',
                'start': '11s',
                'end': '20s',
            },
            '3': {
                'number': '3',
                'type': 'primary',
                'start': '21s',
                'end': '30s',
            },
            '4': {
                'number': '4',
                'type': 'primary',
                'start': '31s',
                'end': '40s',
            },
        }
        partition_data = ('/dev/sda', 'extended', '41s', '50s')
        self.assertRaises(partitioned.EnumerateException,
                          partitioned._get_partition_number,
                          *partition_data)

        _get_cached_info.return_value = {'partition table': 'gpt'}
        _get_cached_partitions.return_value = {}
        self.assertRaises(partitioned.EnumerateException,
                          partitioned._get_partition_number,
                          *partition_data)

    @patch('states.partitioned._get_cached_info')
    @patch('states.partitioned._get_cached_partitions')
    def test_get_partition_number_logial(self, _get_cached_partitions,
                                         _get_cached_info):
        _get_cached_info.return_value = {'partition table': 'msdos'}
        _get_cached_partitions.return_value = {}
        partition_data = ('/dev/sda', 'logical', '0s', '10s')
        self.assertRaises(partitioned.EnumerateException,
                          partitioned._get_partition_number,
                          *partition_data)

        _get_cached_partitions.return_value = {
            '1': {
                'number': '1',
                'type': 'primary',
                'start': '0s',
                'end': '10s',
            },
        }
        partition_data = ('/dev/sda', 'logical', '12s', '15s')
        self.assertRaises(partitioned.EnumerateException,
                          partitioned._get_partition_number,
                          *partition_data)

        _get_cached_partitions.return_value = {
            '1': {
                'number': '1',
                'type': 'primary',
                'start': '0s',
                'end': '10s',
            },
            '2': {
                'number': '2',
                'type': 'extended',
                'start': '11s',
                'end': '20s',
            },
        }
        self.assertEqual(
            partitioned._get_partition_number(*partition_data), '5')

        _get_cached_partitions.return_value = {
            '1': {
                'number': '1',
                'type': 'primary',
                'start': '0s',
                'end': '10s',
            },
            '2': {
                'number': '2',
                'type': 'extended',
                'start': '11s',
                'end': '20s',
            },
            '5': {
                'number': '5',
                'type': 'logical',
                'start': '12s',
                'end': '15s',
            },
        }
        self.assertEqual(
            partitioned._get_partition_number(*partition_data), '5')

        partition_data = ('/dev/sda', 'logical', '16s', '19s')
        self.assertEqual(
            partitioned._get_partition_number(*partition_data), '6')

    @patch('states.partitioned._get_partition_number')
    @patch('states.partitioned.__salt__')
    def test_mkparted(self, __salt__, _get_partition_number):
        pass


if __name__ == '__main__':
    unittest.main()
