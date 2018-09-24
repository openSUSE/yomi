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
                    'label': True,
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
            'sda': hd, 'sdb': usb, 'sr0': cdrom}[d]
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


if __name__ == '__main__':
    unittest.main()
