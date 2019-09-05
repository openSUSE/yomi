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
from unittest.mock import patch, MagicMock

from salt.exceptions import SaltInvocationError, CommandExecutionError

from modules import images


class ImagesTestCase(unittest.TestCase):

    def test__checksum_url(self):
        '''Test images._checksum_url function'''
        self.assertEqual(
            images._checksum_url('http://example.com/image.xz', 'md5'),
            'http://example.com/image.md5')
        self.assertEqual(
            images._checksum_url('http://example.com/image.ext4', 'md5'),
            'http://example.com/image.ext4.md5')

    def test__curl_cmd(self):
        '''Test images._curl_cmd function'''
        self.assertEqual(
            images._curl_cmd('http://example.com/image.xz'),
            ['curl', 'http://example.com/image.xz'])
        self.assertEqual(
            images._curl_cmd('http://example.com/image.xz', s=None),
            ['curl', '-s', 'http://example.com/image.xz'])
        self.assertEqual(
            images._curl_cmd('http://example.com/image.xz', s='a'),
            ['curl', '-s', 'a', 'http://example.com/image.xz'])
        self.assertEqual(
            images._curl_cmd('http://example.com/image.xz', _long=None),
            ['curl', '--_long', 'http://example.com/image.xz'])
        self.assertEqual(
            images._curl_cmd('http://example.com/image.xz', _long='a'),
            ['curl', '--_long', 'a', 'http://example.com/image.xz'])

    def test__fetch_file(self):
        '''Test images._fetch_file function'''
        salt_mock = {
            'cmd.run_stdout': MagicMock(return_value='stdout'),
        }

        with patch.dict(images.__salt__, salt_mock):
            self.assertEqual(
                images._fetch_file('http://url'), 'stdout')
            salt_mock['cmd.run_stdout'].assert_called_with(
                ['curl', '--silent', '--location', 'http://url']
            )

        with patch.dict(images.__salt__, salt_mock):
            self.assertEqual(
                images._fetch_file('http://url', s='a'), 'stdout')
            salt_mock['cmd.run_stdout'].assert_called_with(
                ['curl', '--silent', '--location', '-s', 'a', 'http://url']
            )

    def test__find_filesystem(self):
        '''Test images._find_filesystem function'''
        salt_mock = {
            'cmd.run_stdout': MagicMock(return_value='ext4'),
        }

        with patch.dict(images.__salt__, salt_mock):
            self.assertEqual(
                images._find_filesystem('/dev/sda1'), 'ext4')
            salt_mock['cmd.run_stdout'].assert_called_with(
                ['lsblk', '--noheadings', '--output', 'FSTYPE', '/dev/sda1']
            )

    def test_fetch_checksum(self):
        '''Test images.fetch_checksum function'''
        salt_mock = {
            'cmd.run_stdout': MagicMock(return_value='mychecksum -'),
        }

        with patch.dict(images.__salt__, salt_mock):
            self.assertEqual(
                images.fetch_checksum('http://url/image.xz',
                                      checksum_type='md5'),
                'mychecksum')
            salt_mock['cmd.run_stdout'].assert_called_with(
                ['curl', '--silent', '--location', 'http://url/image.md5']
            )

        with patch.dict(images.__salt__, salt_mock):
            self.assertEqual(
                images.fetch_checksum('http://url/image.ext4',
                                      checksum_type='md5'),
                'mychecksum')
            salt_mock['cmd.run_stdout'].assert_called_with(
                ['curl', '--silent', '--location', 'http://url/image.ext4.md5']
            )

        with patch.dict(images.__salt__, salt_mock):
            self.assertEqual(
                images.fetch_checksum('http://url/image.xz',
                                      checksum_type='sha1', s='a'),
                'mychecksum')
            salt_mock['cmd.run_stdout'].assert_called_with(
                ['curl', '--silent', '--location', '-s', 'a',
                 'http://url/image.sha1']
            )

    def test_dump_invalid_url(self):
        '''Test images.dump function with an invalid URL'''
        with self.assertRaises(SaltInvocationError):
            images.dump('random://example.org', '/dev/sda1')

    def test_dump_invalid_checksum_type(self):
        '''Test images.dump function with an invalid checksum type'''
        with self.assertRaises(SaltInvocationError):
            images.dump('http://example.org/image.xz', '/dev/sda1',
                        checksum_type='crc')

    def test_dump_missing_checksum_type(self):
        '''Test images.dump function with a missing checksum type'''
        with self.assertRaises(SaltInvocationError):
            images.dump('http://example.org/image.xz', '/dev/sda1',
                        checksum='mychecksum')

    def test_dump_download_fail(self):
        '''Test images.dump function when download fails'''
        salt_mock = {
            'cmd.run_all': MagicMock(return_value={
                'retcode': 1,
                'stderr': 'error',
            }),
        }

        with patch.dict(images.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                images.dump('http://example.org/image.ext4', '/dev/sda1')
            salt_mock['cmd.run_all'].assert_called_with(
                'set -eo pipefail ; curl --fail --location --silent '
                'http://example.org/image.ext4 | tee /dev/sda1 '
                '| md5sum', python_shell=True)

    def test_dump_download_fail_gz(self):
        '''Test images.dump function when download fails (gz)'''
        salt_mock = {
            'cmd.run_all': MagicMock(return_value={
                'retcode': 1,
                'stderr': 'error',
            }),
        }

        with patch.dict(images.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                images.dump('http://example.org/image.gz', '/dev/sda1')
            salt_mock['cmd.run_all'].assert_called_with(
                'set -eo pipefail ; curl --fail --location --silent '
                'http://example.org/image.gz | gunzip | tee /dev/sda1 '
                '| md5sum', python_shell=True)

    def test_dump_download_fail_bz2(self):
        '''Test images.dump function when download fails (bz2)'''
        salt_mock = {
            'cmd.run_all': MagicMock(return_value={
                'retcode': 1,
                'stderr': 'error',
            }),
        }

        with patch.dict(images.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                images.dump('http://example.org/image.bz2', '/dev/sda1')
            salt_mock['cmd.run_all'].assert_called_with(
                'set -eo pipefail ; curl --fail --location --silent '
                'http://example.org/image.bz2 | bzip2 -d | tee /dev/sda1 '
                '| md5sum', python_shell=True)

    def test_dump_download_fail_xz(self):
        '''Test images.dump function when download fails (xz)'''
        salt_mock = {
            'cmd.run_all': MagicMock(return_value={
                'retcode': 1,
                'stderr': 'error',
            }),
        }

        with patch.dict(images.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                images.dump('http://example.org/image.xz', '/dev/sda1')
            salt_mock['cmd.run_all'].assert_called_with(
                'set -eo pipefail ; curl --fail --location --silent '
                'http://example.org/image.xz | xz -d | tee /dev/sda1 '
                '| md5sum', python_shell=True)

    def test_dump_download_checksum_fail(self):
        '''Test images.dump function when checksum fails'''
        salt_mock = {
            'cmd.run_all': MagicMock(return_value={
                'retcode': 0,
                'stdout': 'badchecksum',
            }),
        }

        with patch.dict(images.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                images.dump('http://example.org/image.ext4', '/dev/sda1',
                            checksum_type='md5', checksum='checksum')

    def test_dump_download_checksum_fail_fetch(self):
        '''Test images.dump function when checksum fails'''
        salt_mock = {
            'cmd.run_stdout': MagicMock(return_value='checksum -'),
            'cmd.run_all': MagicMock(return_value={
                'retcode': 0,
                'stdout': 'badchecksum',
            }),
        }

        with patch.dict(images.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                images.dump('http://example.org/image.ext4', '/dev/sda1',
                            checksum_type='md5')

    def test_dump_resize_fail_extx(self):
        '''Test images.dump function when resize fails (extx)'''
        salt_mock = {
            'cmd.run_stdout': MagicMock(return_value='ext4'),
            'cmd.run_all': MagicMock(side_effect=[
                {
                    'retcode': 0,
                    'stdout': 'checksum',
                },
                {
                    'retcode': 1,
                    'stderr': 'error',
                }
            ]),
        }

        with patch.dict(images.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                images.dump('http://example.org/image.ext4', '/dev/sda1',
                            checksum_type='md5', checksum='checksum')
            salt_mock['cmd.run_all'].assert_called_with(
                'e2fsck -f -y /dev/sda1; resize2fs /dev/sda1',
                python_shell=True)

    def test_dump_resize_fail_btrfs(self):
        '''Test images.dump function when resize fails (btrfs)'''
        salt_mock = {
            'cmd.run_stdout': MagicMock(return_value='btrfs'),
            'cmd.run_all': MagicMock(side_effect=[
                {
                    'retcode': 0,
                    'stdout': 'checksum',
                },
                {
                    'retcode': 1,
                    'stderr': 'error',
                }
            ]),
        }

        with patch.dict(images.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                images.dump('http://example.org/image.btrfs', '/dev/sda1',
                            checksum_type='md5', checksum='checksum')
            salt_mock['cmd.run_all'].assert_called_with(
                'mount /dev/sda1 /mnt; btrfs filesystem resize max /mnt; '
                'umount /mnt',
                python_shell=True)

    def test_dump_resize_fail_xfs(self):
        '''Test images.dump function when resize fails (xfs)'''
        salt_mock = {
            'cmd.run_stdout': MagicMock(return_value='xfs'),
            'cmd.run_all': MagicMock(side_effect=[
                {
                    'retcode': 0,
                    'stdout': 'checksum',
                },
                {
                    'retcode': 1,
                    'stderr': 'error',
                }
            ]),
        }

        with patch.dict(images.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                images.dump('http://example.org/image.xfs', '/dev/sda1',
                            checksum_type='md5', checksum='checksum')
            salt_mock['cmd.run_all'].assert_called_with(
                'mount /dev/sda1 /mnt; xfs_growfs /mnt; umount /mnt',
                python_shell=True)

    def test_dump_resize(self):
        '''Test images.dump function'''
        salt_mock = {
            'cmd.run_stdout': MagicMock(return_value='ext4'),
            'cmd.run_all': MagicMock(side_effect=[
                {
                    'retcode': 0,
                    'stdout': 'checksum',
                },
                {
                    'retcode': 0,
                }
            ]),
            'cmd.run': MagicMock(return_value=''),
        }

        with patch.dict(images.__salt__, salt_mock):
            self.assertEqual(
                images.dump('http://example.org/image.ext4', '/dev/sda1',
                            checksum_type='md5', checksum='checksum'),
                'checksum')
            salt_mock['cmd.run'].assert_called_with('sync')
