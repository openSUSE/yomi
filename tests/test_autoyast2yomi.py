# -*- coding: utf-8 -*-
#
# Author: Alberto Planas <aplanas@suse.com>
#
# Copyright 2019 SUSE LLC.
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

import os.path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import autoyast2yomi


class AutoYaST2YomiTestCase(unittest.TestCase):

    def _parse_xml(self, name):
        name = os.path.join(os.path.dirname(__file__),
                            'fixtures/{}'.format(name))
        return ET.parse(name)

    def setUp(self):
        self.maxDiff = None

    def test__find(self):
        control = self._parse_xml('ay_single_ext3.xml')
        general = autoyast2yomi.Convert._find(control.getroot(), 'general')
        self.assertEqual(general.tag,
                         '{http://www.suse.com/1.0/yast2ns}general')

        non_existent = autoyast2yomi.Convert._find(control, 'non-existent')
        self.assertIsNone(non_existent)

    def test__get_tag(self):
        control = ET.fromstring(
            '<a xmlns="http://www.suse.com/1.0/yast2ns"><b/></a>')
        self.assertEqual(autoyast2yomi.Convert._get_tag(control[0]), 'b')

    def test__get_type(self):
        control = ET.fromstring(
            '<a xmlns="http://www.suse.com/1.0/yast2ns" '
            'xmlns:config="http://www.suse.com/1.0/configns">'
            '<b config:type="integer"/></a>')
        self.assertEqual(autoyast2yomi.Convert._get_type(control[0]),
                         'integer')

        control = ET.fromstring(
            '<a xmlns="http://www.suse.com/1.0/yast2ns" '
            'xmlns:config="http://www.suse.com/1.0/configns">'
            '<b/></a>')
        self.assertIsNone(autoyast2yomi.Convert._get_type(control[0]))

    def test__get_text(self):
        control = ET.fromstring(
            '<a xmlns="http://www.suse.com/1.0/yast2ns"><b>text</b></a>')
        value = autoyast2yomi.Convert._get_text(control[0])
        self.assertEqual(value, 'text')

        non_text = autoyast2yomi.Convert._get_text(None)
        self.assertIsNone(non_text)

    def test__get_bool(self):
        control = ET.fromstring(
            '<a xmlns="http://www.suse.com/1.0/yast2ns"><b>true</b>'
            '<c>false</c></a>')
        value = autoyast2yomi.Convert._get_bool(control[0])
        self.assertTrue(value)

        value = autoyast2yomi.Convert._get_bool(control[1])
        self.assertFalse(value)

        non_bool = autoyast2yomi.Convert._get_bool(control)
        self.assertIsNone(non_bool)

    def test__get_int(self):
        control = ET.fromstring(
            '<a xmlns="http://www.suse.com/1.0/yast2ns"><b>0</b>'
            '<c>1</c></a>')
        value = autoyast2yomi.Convert._get_int(control[0])
        self.assertEqual(value, 0)

        value = autoyast2yomi.Convert._get_int(control[1])
        self.assertEqual(value, 1)

        non_int = autoyast2yomi.Convert._get_int(control)
        self.assertIsNone(non_int)

    def test__parse_single_text(self):
        control = ET.fromstring(
            '<a xmlns="http://www.suse.com/1.0/yast2ns">text</a>')
        self.assertEqual(autoyast2yomi.Convert._parse(control), {
            'a': 'text'
        })

    def test__parse_single_bool(self):
        control = ET.fromstring(
            '<a xmlns="http://www.suse.com/1.0/yast2ns" '
            'xmlns:config="http://www.suse.com/1.0/configns" '
            'config:type="boolean">true</a>')
        self.assertEqual(autoyast2yomi.Convert._parse(control), {
            'a': True
        })

    def test__parse_single_int(self):
        control = ET.fromstring(
            '<a xmlns="http://www.suse.com/1.0/yast2ns" '
            'xmlns:config="http://www.suse.com/1.0/configns" '
            'config:type="integer">10</a>')
        self.assertEqual(autoyast2yomi.Convert._parse(control), {
            'a': 10
        })

    def test__parse_single_list(self):
        control = ET.fromstring(
            '<a xmlns="http://www.suse.com/1.0/yast2ns" '
            'xmlns:config="http://www.suse.com/1.0/configns" '
            'config:type="list"><b>one</b><b>two</b></a>')
        self.assertEqual(autoyast2yomi.Convert._parse(control), {
            'a': ['one', 'two']
        })

    def test__parse_single_dict(self):
        control = ET.fromstring(
            '<a xmlns="http://www.suse.com/1.0/yast2ns">'
            '<b>text</b><c>other</c></a>')
        self.assertEqual(autoyast2yomi.Convert._parse(control), {
            'a': {'b': 'text', 'c': 'other'}
        })

    def test__parse_complex(self):
        control = self._parse_xml('ay_complex.xml').getroot()
        self.assertEqual(autoyast2yomi.Convert._parse(control), {
            'profile': {
                'partitioning': [
                    {
                        'device': '/dev/sda',
                        'disklabel': 'gpt',
                        'enable_snapshots': True,
                        'initialize': True,
                        'partitions': [
                            {
                                'bcache_backing_for': '/dev/bcache0',
                                'bcache_caching_for': ['/dev/bcache0'],
                                'create': False,
                                'create_subvolumes': False,
                                'crypt_fs': False,
                                'filesystem': 'btrfs',
                                'fstopt': ('ro,noatime,user,data=ordered,'
                                           'acl,user_xattr'),
                                'label': 'mydata',
                                'lv_name': 'opt_lv',
                                'lvm_group': 'system',
                                'mkfs_options': '-I 128',
                                'mount': '/',
                                'mountby': 'label',
                                'partition_id': 131,
                                'partition_nr': 1,
                                'partition_type': 'primary',
                                'pool': False,
                                'raid_name': '/dev/md/0',
                                'raid_options': {
                                    'chunk_size': '4',
                                    'device_order': ['/dev/sdb2',
                                                     '/dev/sda1'],
                                    'parity_algorithm': 'left_asymmetric',
                                    'raid_type': 'raid1'
                                },
                                'resize': False,
                                'size': '10G',
                                'stripes': 2,
                                'stripesize': 4,
                                'subvolumes': ['tmp',
                                               'opt',
                                               'srv',
                                               'var/crash',
                                               'var/lock',
                                               'var/run',
                                               'var/tmp',
                                               'var/spool'],
                                'subvolumes_prefix': '@',
                                'used_pool': 'my_thin_pool',
                                'uuid': 'UUID'
                            }
                        ],
                        'type': 'CT_DISK',
                        'use': 'all'
                    }
                ]
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_config_single_ext3(self, logging):
        control = self._parse_xml('ay_single_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_config()
        self.assertEqual(convert.pillar, {
            'config': {
                'events': True,
                'reboot': True,
                'snapper': False,
                'locale': 'en_GB',
                'keymap': 'de-nodeadkeys',
                'timezone': 'Europe/Berlin',
                'hostname': 'linux-bqua',
                'target': 'multi-user',
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_partitions_single_ext3(self, logging):
        control = self._parse_xml('ay_single_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_partitions()
        self.assertEqual(convert.pillar, {
            'partitions': {
                'devices': {
                    '/dev/sda': {
                        'label': 'gpt',
                        'partitions': [
                            {
                                'number': 1,
                                'size': '1M',
                                'type': 'boot',
                            },
                            {
                                'number': 2,
                                'size': '2G',
                                'type': 'swap',
                            },
                            {
                                'number': 3,
                                'size': 'rest',
                                'type': 'linux',
                            },
                        ]
                    }
                }
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_partitions_lvm_ext3(self, logging):
        control = self._parse_xml('ay_lvm_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_partitions()
        self.assertEqual(convert.pillar, {
            'partitions': {
                'devices': {
                    '/dev/sda': {
                        'label': 'gpt',
                        'partitions': [
                            {
                                'number': 1,
                                'size': 'rest',
                                'type': 'lvm',
                            }
                        ]
                    }
                }
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_partitions_raid_ext3(self, logging):
        control = self._parse_xml('ay_raid_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_partitions()
        self.assertEqual(convert.pillar, {
            'partitions': {
                'devices': {
                    '/dev/sda': {
                        'label': 'gpt',
                        'partitions': [
                            {
                                'number': 1,
                                'size': '20G',
                                'type': 'linux',
                            },
                            {
                                'number': 2,
                                'size': 'rest',
                                'type': 'raid',
                            },
                        ]
                    },
                    '/dev/sdb': {
                        'partitions': [
                            {
                                'number': 1,
                                'size': 'rest',
                                'type': 'raid',
                            },
                        ]
                    },
                    '/dev/md/0': {
                        'partitions': [
                            {
                                'number': 1,
                                'size': '40G',
                                'type': 'linux',
                            },
                            {
                                'number': 2,
                                'size': '10G',
                                'type': 'linux',
                            },
                        ]
                    },
                }
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_lvm_ext3(self, logging):
        control = self._parse_xml('ay_lvm_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_lvm()
        self.assertEqual(convert.pillar, {
            'lvm': {
                'system': {
                    'devices': ['/dev/sda1'],
                    'physicalextentsize': '4M',
                    'volumes': [
                        {
                            'name': 'user_lv',
                            'size': '15G',
                        },
                        {
                            'name': 'opt_lv',
                            'size': '10G',
                        },
                        {
                            'name': 'var_lv',
                            'size': '1G',
                        },
                    ]
                }
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_raid_ext3(self, logging):
        control = self._parse_xml('ay_raid_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_raid()
        self.assertEqual(convert.pillar, {
            'raid': {
                '/dev/md/0': {
                    'level': 'raid1',
                    'devices': [
                        '/dev/sda2',
                        '/dev/sdb1'
                    ],
                    'chunk': '4',
                    'parity': 'left-asymmetric',
                }
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_filesystems_single_ext3(self, logging):
        control = self._parse_xml('ay_single_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_filesystems()
        self.assertEqual(convert.pillar, {
            'filesystems': {
                '/dev/sda2': {
                    'filesystem': 'swap',
                    'mountpoint': 'swap',
                },
                '/dev/sda3': {
                    'filesystem': 'ext3',
                    'mountpoint': '/',
                },
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_filesystems_single_btrfs(self, logging):
        control = self._parse_xml('ay_single_btrfs.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_filesystems()
        self.assertEqual(convert.pillar, {
            'filesystems': {
                '/dev/sda2': {
                    'filesystem': 'swap',
                    'mountpoint': 'swap',
                },
                '/dev/sda3': {
                    'filesystem': 'btrfs',
                    'mountpoint': '/',
                    'subvolumes': {
                        'prefix': '@',
                        'subvolume': [
                            {'path': 'tmp'},
                            {'path': 'opt'},
                            {'path': 'srv'},
                            {
                                'path': 'var/lib/pgsql',
                                'copy_on_write': False,
                            },
                        ]
                    }
                }
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_filesystems_lvm_ext3(self, logging):
        control = self._parse_xml('ay_lvm_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_filesystems()
        self.assertEqual(convert.pillar, {
            'filesystems': {
                '/dev/system/user_lv': {
                    'filesystem': 'ext3',
                    'mountpoint': '/usr',
                },
                '/dev/system/opt_lv': {
                    'filesystem': 'ext3',
                    'mountpoint': '/opt',
                },
                '/dev/system/var_lv': {
                    'filesystem': 'ext3',
                    'mountpoint': '/var',
                },
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_filesystems_raid_ext3(self, logging):
        control = self._parse_xml('ay_raid_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_filesystems()
        self.assertEqual(convert.pillar, {
            'filesystems': {
                '/dev/sda1': {
                    'filesystem': 'ext3',
                    'mountpoint': '/',
                },
                '/dev/md/0p1': {
                    'filesystem': 'ext3',
                    'mountpoint': '/home',
                },
                '/dev/md/0p2': {
                    'filesystem': 'ext3',
                    'mountpoint': '/srv',
                },
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_bootloader(self, logging):
        control = self._parse_xml('ay_single_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_bootloader()
        self.assertEqual(convert.pillar, {
            'bootloader': {
                'device': '/dev/sda',
                'timeout': 10,
                'kernel': ('splash=silent quiet nomodeset vga=0x317 '
                           'noibrs noibpb nopti nospectre_v2 nospectre_v1 '
                           'l1tf=off nospec_store_bypass_disable '
                           'no_stf_barrier mds=off mitigations=off'),
                'terminal': 'serial',
                'serial_command': ('serial --speed=115200 --unit=0 '
                                   '--word=8 --parity=no --stop=1'),
                'gfxmode': '1280x1024x24',
                'theme': True,
                'disable_os_prober': True,
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_software(self, logging):
        control = self._parse_xml('ay_single_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_software()
        self.assertEqual(convert.pillar, {
            'software': {
                'config': {
                    'minimal': True,
                },
                'repositories': {
                    'SLES SDK': 'cd:///sdk',
                    'yast2_head': ('https://download.opensuse.org/repositories'
                                   '/YaST:/Head/openSUSE_Leap_15.1/'),
                },
                'packages': [
                    'product:SLED',
                    'pattern:directory_server',
                    'apache',
                    'postfix',
                    'kernel-default',
                ],
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_suseconnect(self, logging):
        control = self._parse_xml('ay_single_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_suseconnect()
        self.assertEqual(convert.pillar, {
            'suseconnect': {
                'config': {
                    'regcode': 'MY_SECRET_REGCODE',
                    'email': 'tux@example.com',
                    'url': 'https://smt.example.com',
                },
                'products': ['sle-module-basesystem/15.1/x86_64'],
                'packages': [
                    'pattern:apparmor',
                    'yast2-cim',
                ],
            },
        })

    @patch('autoyast2yomi.logging')
    def test__convert_salt_minion(self, logging):
        control = self._parse_xml('ay_single_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_salt_minion()
        self.assertEqual(convert.pillar, {
            'salt-minion': {
                'configure': True,
            }
        })

    @patch('autoyast2yomi.logging')
    def test__convert_services(self, logging):
        control = self._parse_xml('ay_single_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        convert._convert_services()
        self.assertEqual(convert.pillar, {
            'services': {
                'enabled': ['sshd.service', 'cups.socket'],
                'disabled': ['libvirtd.service', 'cups.service'],
            }
        })

    def test__password(self):
        self.assertEqual(autoyast2yomi.Convert._password({}), None)
        self.assertEqual(autoyast2yomi.Convert._password({
            'user_password': 'linux'
        }, salt='$1$wYJUgpM5'), '$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0')
        self.assertEqual(autoyast2yomi.Convert._password({
            'user_password': '$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0',
            'encrypted': True,
        }), '$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0')

    @patch('autoyast2yomi.logging')
    @patch('autoyast2yomi.Convert._password')
    def test__convert_users(self, _password, logging):
        control = self._parse_xml('ay_single_ext3.xml')
        convert = autoyast2yomi.Convert(control)
        convert._control = autoyast2yomi.Convert._parse(control.getroot())
        _password.return_value = '<hash>'
        convert._convert_users()
        self.assertEqual(convert.pillar, {
            'users': [
                {
                    'username': 'root',
                    'password': '<hash>',
                    'certificates': [
                        ('AAAAB3NzaC1yc2EAAAADAQABAAABAQDKLt1vnW2vTJpBp3VK91'
                         'rFsBvpY97NljsVLdgUrlPbZ/L51FerQQ+djQ/ivDASQjO+567n'
                         'MGqfYGFA/De1EGMMEoeShza67qjNi14L1HBGgVojaNajMR/NI2'
                         'd1kDyvsgRy7D7FT5UGGUNT0dlcSD3b85zwgHeYLidgcGIoKeRi'
                         '7HpVDOOTyhwUv4sq3ubrPCWARgPeOLdVFa9clC8PTZdxSeKp4j'
                         'pNjIHEyREPin2Un1luCIPWrOYyym7aRJEPopCEqBA9Hvfwpbuw'
                         'BI5F0uIWZgSQLfpwW86599fBo/PvMDa96DpxH1VlzJlAIHQsMk'
                         'MHbsCazPNC0++Kp5ZVERiH')
                    ]
                },
                {
                    'username': 'tux',
                    'password': '<hash>',
                }
            ]
        })
