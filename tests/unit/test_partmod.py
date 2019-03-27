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

from salt.exceptions import SaltInvocationError

from disk import ParseException
from modules import partmod
from modules import filters


class PartmodTestCase(unittest.TestCase):

    @patch('modules.partmod.__grains__')
    def test_prepare_partition_data_fails_fs_type(self, __grains__):
        partitions = {
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'error',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        with self.assertRaises(SaltInvocationError) as cm:
            partmod.prepare_partition_data(partitions)
        self.assertTrue('type error not recognized' in str(cm.exception))

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_fails_units_invalid(self, __salt__,
                                                        __grains__):
        partitions = {
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': '1Kilo',
                            'type': 'swap',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        with self.assertRaises(ParseException) as cm:
            partmod.prepare_partition_data(partitions)
        self.assertTrue('Kilo not recognized' in str(cm.exception))

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_fails_units_initial_gap(self, __salt__,
                                                            __grains__):
        partitions = {
            'config': {
                'initial_gap': '1024kB',
            },
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': '1MB',
                            'type': 'swap',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        with self.assertRaises(SaltInvocationError) as cm:
            partmod.prepare_partition_data(partitions)
        self.assertTrue('Units needs to be' in str(cm.exception))

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_bios_no_gap(self, __salt__, __grains__):
        partitions = {
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/sda': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sda1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
        })

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_bios_msdos_no_gap(self, __salt__,
                                                      __grains__):
        partitions = {
            'config': {
                'label': 'msdos',
            },
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/sda': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sda1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
        })

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_bios_local_msdos_no_gap(self, __salt__,
                                                            __grains__):
        partitions = {
            'devices': {
                '/dev/sda': {
                    'label': 'msdos',
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/sda': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sda1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
        })

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_bios_gpt_no_gap(self, __salt__,
                                                    __grains__):
        partitions = {
            'config': {
                'label': 'gpt',
            },
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/sda': {
                'label': 'gpt',
                'pmbr_boot': True,
                'partitions': [
                    {
                        'part_id': '/dev/sda1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
        })

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_bios_local_gpt_no_gap(self, __salt__,
                                                          __grains__):
        partitions = {
            'devices': {
                '/dev/sda': {
                    'label': 'gpt',
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/sda': {
                'label': 'gpt',
                'pmbr_boot': True,
                'partitions': [
                    {
                        'part_id': '/dev/sda1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
        })

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_gap(self, __salt__, __grains__):
        partitions = {
            'config': {
                'initial_gap': '1MB',
            },
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/sda': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sda1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '1.0MB',
                        'end': '100%',
                    },
                ],
            },
        })

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_local_gap(self, __salt__, __grains__):
        partitions = {
            'devices': {
                '/dev/sda': {
                    'initial_gap': '1MB',
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/sda': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sda1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '1.0MB',
                        'end': '100%',
                    },
                ],
            },
        })

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_fails_rest(self, __salt__, __grains__):
        partitions = {
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'swap',
                        },
                        {
                            'number': 2,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        with self.assertRaises(SaltInvocationError) as cm:
            partmod.prepare_partition_data(partitions)
        self.assertTrue('rest free space' in str(cm.exception))

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_fails_units(self, __salt__, __grains__):
        partitions = {
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': '1%',
                            'type': 'swap',
                        },
                        {
                            'number': 2,
                            'size': '2MB',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        with self.assertRaises(SaltInvocationError) as cm:
            partmod.prepare_partition_data(partitions)
        self.assertTrue('Units needs to be' in str(cm.exception))

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_efi_partitions(self, __salt__, __grains__):
        partitions = {
            'devices': {
                '/dev/sda': {
                    'label': 'gpt',
                    'partitions': [
                        {
                            'number': 1,
                            'size': '500MB',
                            'type': 'efi',
                        },
                        {
                            'number': 2,
                            'size': '10000MB',
                            'type': 'linux',
                        },
                        {
                            'number': 3,
                            'size': '5000MB',
                            'type': 'swap',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = True
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/sda': {
                'label': 'gpt',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sda1',
                        'part_type': 'primary',
                        'fs_type': 'fat16',
                        'flags': ['esp'],
                        'start': '0MB',
                        'end': '500.0MB',
                    },
                    {
                        'part_id': '/dev/sda2',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '500.0MB',
                        'end': '10500.0MB',
                    },
                    {
                        'part_id': '/dev/sda3',
                        'part_type': 'primary',
                        'fs_type': 'linux-swap',
                        'flags': None,
                        'start': '10500.0MB',
                        'end': '15500.0MB',
                    },
                ],
            },
        })

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_bios_muti_label(self, __salt__,
                                                    __grains__):
        partitions = {
            'config': {
                'label': 'msdos',
            },
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
                '/dev/sdb': {
                    'label': 'gpt',
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/sda': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sda1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
            '/dev/sdb': {
                'label': 'gpt',
                'pmbr_boot': True,
                'partitions': [
                    {
                        'part_id': '/dev/sdb1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
        })

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_multi_gap(self, __salt__, __grains__):
        partitions = {
            'config': {
                'initial_gap': '1MB',
            },
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
                '/dev/sdb': {
                    'initial_gap': '2MB',
                    'partitions': [
                        {
                            'number': 1,
                            'size': '20MB',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/sda': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sda1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '1.0MB',
                        'end': '100%',
                    },
                ],
            },
            '/dev/sdb': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sdb1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '2.0MB',
                        'end': '22.0MB',
                    },
                ],
            },
        })

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_lvm(self, __salt__, __grains__):
        partitions = {
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'lvm',
                        },
                    ],
                },
                '/dev/sdb': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'lvm',
                        },
                    ],
                },
                '/dev/sdc': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/sda': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sda1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': ['lvm'],
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
            '/dev/sdb': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sdb1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': ['lvm'],
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
            '/dev/sdc': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sdc1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
        })

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_raid(self, __salt__, __grains__):
        partitions = {
            'devices': {
                '/dev/sda': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'raid',
                        },
                    ],
                },
                '/dev/sdb': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'raid',
                        },
                    ],
                },
                '/dev/sdc': {
                    'partitions': [
                        {
                            'number': 1,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/sda': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sda1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': ['raid'],
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
            '/dev/sdb': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sdb1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': ['raid'],
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
            '/dev/sdc': {
                'label': 'msdos',
                'pmbr_boot': False,
                'partitions': [
                    {
                        'part_id': '/dev/sdc1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '0%',
                        'end': '100%',
                    },
                ],
            },
        })

    @patch('modules.partmod.__grains__')
    @patch('modules.partmod.__salt__')
    def test_prepare_partition_data_bios_gpt_post_raid(self, __salt__, __grains__):
        partitions = {
            'devices': {
                '/dev/md0': {
                    'label': 'gpt',
                    'partitions': [
                        {
                            'number': 1,
                            'size': '8MB',
                            'type': 'boot',
                        },
                        {
                            'number': 2,
                            'size': 'rest',
                            'type': 'linux',
                        },
                    ],
                },
            },
        }
        __grains__.__getitem__.return_value = False
        __salt__.__getitem__.return_value = filters.is_raid
        self.assertEqual(partmod.prepare_partition_data(partitions), {
            '/dev/md0': {
                'label': 'gpt',
                'pmbr_boot': True,
                'partitions': [
                    {
                        'part_id': '/dev/md0p1',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': ['bios_grub'],
                        'start': '0MB',
                        'end': '8.0MB',
                    },
                    {
                        'part_id': '/dev/md0p2',
                        'part_type': 'primary',
                        'fs_type': 'ext2',
                        'flags': None,
                        'start': '8.0MB',
                        'end': '100%',
                    },
                ],
            },
        })


if __name__ == '__main__':
    unittest.main()
