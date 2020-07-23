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

import unittest
from unittest.mock import patch, MagicMock

from states import suseconnect

from salt.exceptions import CommandExecutionError


class SUSEConnectTestCase(unittest.TestCase):
    def test__status_registered(self):
        salt_mock = {
            "suseconnect.status": MagicMock(
                return_value=[
                    {
                        "identifier": "SLES",
                        "version": "15.2",
                        "arch": "x86_64",
                        "status": "Registered",
                        "subscription_status": "ACTIVE",
                    },
                    {
                        "identifier": "sle-module-basesystem",
                        "version": "15.2",
                        "arch": "x86_64",
                        "status": "Registered",
                    },
                    {
                        "identifier": "sle-module-server-applications",
                        "version": "15.2",
                        "arch": "x86_64",
                        "status": "Registered",
                    },
                ]
            ),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(
                suseconnect._status(None),
                (
                    [
                        "SLES/15.2/x86_64",
                        "sle-module-basesystem/15.2/x86_64",
                        "sle-module-server-applications/15.2/x86_64",
                    ],
                    ["SLES/15.2/x86_64"],
                ),
            )

    def test__status_unregistered(self):
        salt_mock = {
            "suseconnect.status": MagicMock(
                return_value=[
                    {
                        "identifier": "openSUSE",
                        "version": "20191014",
                        "arch": "x86_64",
                        "status": "Not Registered",
                    },
                ]
            ),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(suseconnect._status(None), ([], []))

    @patch("states.suseconnect._status")
    def test__is_registered_default_product(self, _status):
        _status.return_value = (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"])
        self.assertTrue(suseconnect._is_registered(product=None, root=None))

    @patch("states.suseconnect._status")
    def test__is_registered_product(self, _status):
        _status.return_value = (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"])
        self.assertTrue(
            suseconnect._is_registered(product="SLES/15.2/x86_64", root=None)
        )

    @patch("states.suseconnect._status")
    def test__is_registered_default_product_unregistered(self, _status):
        _status.return_value = ([], [])
        self.assertFalse(suseconnect._is_registered(product=None, root=None))

    @patch("states.suseconnect._status")
    def test__is_registered_product_unregistered(self, _status):
        _status.return_value = ([], [])
        self.assertFalse(
            suseconnect._is_registered(product="SLES/15.2/x86_64", root=None)
        )

    @patch("states.suseconnect._status")
    def test__is_registered_other_product_unregistered(self, _status):
        _status.return_value = ([], ["SLES/15.2/x86_64"])
        self.assertFalse(
            suseconnect._is_registered(product="openSUSE/15.2/x86_64", root=None)
        )

    @patch("states.suseconnect._status")
    def test_registered_default_product(self, _status):
        _status.return_value = (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"])
        result = suseconnect.registered("my_setup", "regcode")
        self.assertEqual(
            result,
            {
                "name": "my_setup",
                "result": True,
                "changes": {},
                "comment": ["Product or module default already registered"],
            },
        )

    @patch("states.suseconnect._status")
    def test_registered_named_product(self, _status):
        _status.return_value = (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"])
        result = suseconnect.registered("SLES/15.2/x86_64", "regcode")
        self.assertEqual(
            result,
            {
                "name": "SLES/15.2/x86_64",
                "result": True,
                "changes": {},
                "comment": ["Product or module SLES/15.2/x86_64 already registered"],
            },
        )

    @patch("states.suseconnect._status")
    def test_registered_product(self, _status):
        _status.return_value = (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"])
        result = suseconnect.registered(
            "my_setup", "regcode", product="SLES/15.2/x86_64"
        )
        self.assertEqual(
            result,
            {
                "name": "my_setup",
                "result": True,
                "changes": {},
                "comment": ["Product or module SLES/15.2/x86_64 already registered"],
            },
        )

    @patch("states.suseconnect._status")
    def test_registered_test(self, _status):
        _status.return_value = ([], [])

        opts_mock = {"test": True}
        with patch.dict(suseconnect.__opts__, opts_mock):
            result = suseconnect.registered("my_setup", "regcode")
            self.assertEqual(
                result,
                {
                    "name": "my_setup",
                    "result": None,
                    "changes": {"default": True},
                    "comment": ["Product or module default would be registered"],
                },
            )

    @patch("states.suseconnect._status")
    def test_registered_fail_register(self, _status):
        _status.return_value = ([], [])

        opts_mock = {"test": False}
        salt_mock = {
            "suseconnect.register": MagicMock(
                side_effect=CommandExecutionError("some error")
            )
        }
        with patch.dict(suseconnect.__salt__, salt_mock), patch.dict(
            suseconnect.__opts__, opts_mock
        ):
            result = suseconnect.registered("my_setup", "regcode")
            self.assertEqual(
                result,
                {
                    "name": "my_setup",
                    "result": False,
                    "changes": {},
                    "comment": ["Error registering default: some error"],
                },
            )

    @patch("states.suseconnect._status")
    def test_registered_fail_register_end(self, _status):
        _status.return_value = ([], [])

        opts_mock = {"test": False}
        salt_mock = {"suseconnect.register": MagicMock()}
        with patch.dict(suseconnect.__salt__, salt_mock), patch.dict(
            suseconnect.__opts__, opts_mock
        ):
            result = suseconnect.registered("my_setup", "regcode")
            self.assertEqual(
                result,
                {
                    "name": "my_setup",
                    "result": False,
                    "changes": {"default": True},
                    "comment": ["Product or module default failed to register"],
                },
            )

    @patch("states.suseconnect._status")
    def test_registered_succeed_register(self, _status):
        _status.side_effect = [
            ([], []),
            (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"]),
        ]

        opts_mock = {"test": False}
        salt_mock = {"suseconnect.register": MagicMock()}
        with patch.dict(suseconnect.__salt__, salt_mock), patch.dict(
            suseconnect.__opts__, opts_mock
        ):
            result = suseconnect.registered("my_setup", "regcode")
            self.assertEqual(
                result,
                {
                    "name": "my_setup",
                    "result": True,
                    "changes": {"default": True},
                    "comment": ["Product or module default registered"],
                },
            )
            salt_mock["suseconnect.register"].assert_called_with(
                "regcode", product=None, email=None, url=None, root=None
            )

    @patch("states.suseconnect._status")
    def test_registered_succeed_register_params(self, _status):
        _status.side_effect = [
            ([], []),
            (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"]),
        ]

        opts_mock = {"test": False}
        salt_mock = {"suseconnect.register": MagicMock()}
        with patch.dict(suseconnect.__salt__, salt_mock), patch.dict(
            suseconnect.__opts__, opts_mock
        ):
            result = suseconnect.registered(
                "my_setup",
                "regcode",
                product="SLES/15.2/x86_64",
                email="user@example.com",
                url=None,
                root=None,
            )
            self.assertEqual(
                result,
                {
                    "name": "my_setup",
                    "result": True,
                    "changes": {"SLES/15.2/x86_64": True},
                    "comment": ["Product or module SLES/15.2/x86_64 registered"],
                },
            )
            salt_mock["suseconnect.register"].assert_called_with(
                "regcode",
                product="SLES/15.2/x86_64",
                email="user@example.com",
                url=None,
                root=None,
            )

    @patch("states.suseconnect._status")
    def test_deregistered_default_product(self, _status):
        _status.return_value = ([], [])
        result = suseconnect.deregistered("my_setup")
        self.assertEqual(
            result,
            {
                "name": "my_setup",
                "result": True,
                "changes": {},
                "comment": ["Product or module default already deregistered"],
            },
        )

    @patch("states.suseconnect._status")
    def test_deregistered_named_product(self, _status):
        _status.return_value = ([], [])
        result = suseconnect.deregistered("SLES/15.2/x86_64")
        self.assertEqual(
            result,
            {
                "name": "SLES/15.2/x86_64",
                "result": True,
                "changes": {},
                "comment": [
                    "Product or module SLES/15.2/x86_64 already deregistered"
                ],
            },
        )

    @patch("states.suseconnect._status")
    def test_deregistered_other_named_product(self, _status):
        _status.return_value = (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"])
        result = suseconnect.deregistered("openSUSE/15.2/x86_64")
        self.assertEqual(
            result,
            {
                "name": "openSUSE/15.2/x86_64",
                "result": True,
                "changes": {},
                "comment": [
                    "Product or module openSUSE/15.2/x86_64 already deregistered"
                ],
            },
        )

    @patch("states.suseconnect._status")
    def test_deregistered_product(self, _status):
        _status.return_value = ([], [])
        result = suseconnect.deregistered("my_setup", product="SLES/15.2/x86_64")
        self.assertEqual(
            result,
            {
                "name": "my_setup",
                "result": True,
                "changes": {},
                "comment": [
                    "Product or module SLES/15.2/x86_64 already deregistered"
                ],
            },
        )

    @patch("states.suseconnect._status")
    def test_deregistered_test(self, _status):
        _status.return_value = (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"])

        opts_mock = {"test": True}
        with patch.dict(suseconnect.__opts__, opts_mock):
            result = suseconnect.deregistered("my_setup")
            self.assertEqual(
                result,
                {
                    "name": "my_setup",
                    "result": None,
                    "changes": {"default": True},
                    "comment": ["Product or module default would be deregistered"],
                },
            )

    @patch("states.suseconnect._status")
    def test_deregistered_fail_deregister(self, _status):
        _status.return_value = (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"])

        opts_mock = {"test": False}
        salt_mock = {
            "suseconnect.deregister": MagicMock(
                side_effect=CommandExecutionError("some error")
            )
        }
        with patch.dict(suseconnect.__salt__, salt_mock), patch.dict(
            suseconnect.__opts__, opts_mock
        ):
            result = suseconnect.deregistered("my_setup")
            self.assertEqual(
                result,
                {
                    "name": "my_setup",
                    "result": False,
                    "changes": {},
                    "comment": ["Error deregistering default: some error"],
                },
            )

    @patch("states.suseconnect._status")
    def test_deregistered_fail_deregister_end(self, _status):
        _status.return_value = (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"])

        opts_mock = {"test": False}
        salt_mock = {"suseconnect.deregister": MagicMock()}
        with patch.dict(suseconnect.__salt__, salt_mock), patch.dict(
            suseconnect.__opts__, opts_mock
        ):
            result = suseconnect.deregistered("my_setup")
            self.assertEqual(
                result,
                {
                    "name": "my_setup",
                    "result": False,
                    "changes": {"default": True},
                    "comment": ["Product or module default failed to deregister"],
                },
            )

    @patch("states.suseconnect._status")
    def test_deregistered_succeed_deregister(self, _status):
        _status.side_effect = [
            (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"]),
            ([], []),
        ]

        opts_mock = {"test": False}
        salt_mock = {"suseconnect.deregister": MagicMock()}
        with patch.dict(suseconnect.__salt__, salt_mock), patch.dict(
            suseconnect.__opts__, opts_mock
        ):
            result = suseconnect.deregistered("my_setup")
            self.assertEqual(
                result,
                {
                    "name": "my_setup",
                    "result": True,
                    "changes": {"default": True},
                    "comment": ["Product or module default deregistered"],
                },
            )
            salt_mock["suseconnect.deregister"].assert_called_with(
                product=None, url=None, root=None
            )

    @patch("states.suseconnect._status")
    def test_deregistered_succeed_register_params(self, _status):
        _status.side_effect = [
            (["SLES/15.2/x86_64"], ["SLES/15.2/x86_64"]),
            ([], []),
        ]

        opts_mock = {"test": False}
        salt_mock = {"suseconnect.deregister": MagicMock()}
        with patch.dict(suseconnect.__salt__, salt_mock), patch.dict(
            suseconnect.__opts__, opts_mock
        ):
            result = suseconnect.deregistered(
                "my_setup", product="SLES/15.2/x86_64", url=None, root=None
            )
            self.assertEqual(
                result,
                {
                    "name": "my_setup",
                    "result": True,
                    "changes": {"SLES/15.2/x86_64": True},
                    "comment": ["Product or module SLES/15.2/x86_64 deregistered"],
                },
            )
            salt_mock["suseconnect.deregister"].assert_called_with(
                product="SLES/15.2/x86_64", url=None, root=None
            )
