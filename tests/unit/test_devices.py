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

import unittest
from unittest.mock import patch

from modules import devices


class DevicesTestCase(unittest.TestCase):

    def test_udev(self):
        self.assertEqual(devices._udev({'A': {'B': 1}}, 'a.b'), 1)
        self.assertEqual(devices._udev({'A': {'B': 1}}, 'A.B'), 1)
        self.assertEqual(devices._udev({'A': {'B': 1}}, 'a.c'), 'n/a')
        self.assertEqual(devices._udev({'A': [1, 2]}, 'a.b'), 'n/a')
        self.assertEqual(devices._udev({'A': {'B': 1}}, ''),
                         {'A': {'B': 1}})

    def test_match(self):
        self.assertTrue(devices._match({'A': {'B': 1}}, {'a.b': 1}))
        self.assertFalse(devices._match({'A': {'B': 1}}, {'a.b': 2}))
        self.assertTrue(devices._match({'A': {'B': 1}}, {'a.b': [1, 2]}))
        self.assertFalse(devices._match({'A': {'B': 1}}, {'a.b': [2, 3]}))
        self.assertTrue(devices._match({'A': {'B': [1, 2]}}, {'a.b': 1}))
        self.assertTrue(devices._match({'A': {'B': [1, 2]}}, {'a.b': [1, 3]}))
        self.assertFalse(devices._match({'A': {'B': [1, 2]}}, {'a.b': [3, 4]}))
        self.assertTrue(devices._match({'A': 1}, {}))

    @patch('modules.devices.__grains__')
    @patch('modules.devices.__salt__')
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

        self.assertEqual(devices.filter({'e.id_bus': 'ata'}, {}),
                         ['sda', 'sr0'])
        self.assertEqual(devices.filter({'e.id_bus': 'usb'}, {}), ['sdb'])
        self.assertEqual(devices.filter({'e.id_bus': 'ata'},
                                        {'s': ['cdrom']}), ['sda'])
