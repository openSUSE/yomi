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

import os.path
import unittest
from unittest.mock import patch, MagicMock

from salt.exceptions import CommandExecutionError

from modules import suseconnect


class SUSEConnectTestCase(unittest.TestCase):
    """
    Test cases for salt.modules.suseconnect
    """

    def test_register(self):
        """
        Test suseconnect.register without parameters
        """
        result = {"retcode": 0, "stdout": "Successfully registered system"}
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(
                suseconnect.register("regcode"), "Successfully registered system"
            )
            salt_mock["cmd.run_all"].assert_called_with(
                ["SUSEConnect", "--regcode", "regcode"]
            )

    def test_register_params(self):
        """
        Test suseconnect.register with parameters
        """
        result = {"retcode": 0, "stdout": "Successfully registered system"}
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(
                suseconnect.register(
                    "regcode",
                    product="sle-ha/15.2/x86_64",
                    email="user@example.com",
                    url="https://scc.suse.com",
                    root="/mnt",
                ),
                "Successfully registered system",
            )
            salt_mock["cmd.run_all"].assert_called_with(
                [
                    "SUSEConnect",
                    "--regcode",
                    "regcode",
                    "--product",
                    "sle-ha/15.2/x86_64",
                    "--email",
                    "user@example.com",
                    "--url",
                    "https://scc.suse.com",
                    "--root",
                    "/mnt",
                ]
            )

    def test_register_error(self):
        """
        Test suseconnect.register error
        """
        result = {"retcode": 1, "stdout": "Unknown Registration Code", "stderr": ""}
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                suseconnect.register("regcode")

    def test_deregister(self):
        """
        Test suseconnect.deregister without parameters
        """
        result = {"retcode": 0, "stdout": "Successfully deregistered system"}
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(
                suseconnect.deregister(), "Successfully deregistered system"
            )
            salt_mock["cmd.run_all"].assert_called_with(
                ["SUSEConnect", "--de-register"]
            )

    def test_deregister_params(self):
        """
        Test suseconnect.deregister with parameters
        """
        result = {"retcode": 0, "stdout": "Successfully deregistered system"}
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(
                suseconnect.deregister(
                    product="sle-ha/15.2/x86_64",
                    url="https://scc.suse.com",
                    root="/mnt",
                ),
                "Successfully deregistered system",
            )
            salt_mock["cmd.run_all"].assert_called_with(
                [
                    "SUSEConnect",
                    "--de-register",
                    "--product",
                    "sle-ha/15.2/x86_64",
                    "--url",
                    "https://scc.suse.com",
                    "--root",
                    "/mnt",
                ]
            )

    def test_deregister_error(self):
        """
        Test suseconnect.deregister error
        """
        result = {"retcode": 1, "stdout": "Unknown Product", "stderr": ""}
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                suseconnect.deregister()

    def test_status(self):
        """
        Test suseconnect.status without parameters
        """
        result = {
            "retcode": 0,
            "stdout": '[{"identifier":"SLES","version":"15.2",'
            '"arch":"x86_64","status":"No Registered"}]',
        }
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(
                suseconnect.status(),
                [
                    {
                        "identifier": "SLES",
                        "version": "15.2",
                        "arch": "x86_64",
                        "status": "No Registered",
                    }
                ],
            )
            salt_mock["cmd.run_all"].assert_called_with(["SUSEConnect", "--status"])

    def test_status_params(self):
        """
        Test suseconnect.status with parameters
        """
        result = {
            "retcode": 0,
            "stdout": '[{"identifier":"SLES","version":"15.2",'
            '"arch":"x86_64","status":"No Registered"}]',
        }
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(
                suseconnect.status(root="/mnt"),
                [
                    {
                        "identifier": "SLES",
                        "version": "15.2",
                        "arch": "x86_64",
                        "status": "No Registered",
                    }
                ],
            )
            salt_mock["cmd.run_all"].assert_called_with(
                ["SUSEConnect", "--status", "--root", "/mnt"]
            )

    def test_status_error(self):
        """
        Test suseconnect.status error
        """
        result = {"retcode": 1, "stdout": "Some Error", "stderr": ""}
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                suseconnect.status()

    def test__parse_list_extensions(self):
        """
        Test suseconnect.status error
        """
        fixture = os.path.join(
            os.path.dirname(__file__), "fixtures/list_extensions.txt"
        )
        with open(fixture) as f:
            self.assertEqual(
                suseconnect._parse_list_extensions(f.read()),
                [
                    "sle-module-basesystem/15.2/x86_64",
                    "sle-module-containers/15.2/x86_64",
                    "sle-module-desktop-applications/15.2/x86_64",
                    "sle-module-development-tools/15.2/x86_64",
                    "sle-we/15.2/x86_64",
                    "sle-module-python2/15.2/x86_64",
                    "sle-module-live-patching/15.2/x86_64",
                    "PackageHub/15.2/x86_64",
                    "sle-module-server-applications/15.2/x86_64",
                    "sle-module-legacy/15.2/x86_64",
                    "sle-module-public-cloud/15.2/x86_64",
                    "sle-ha/15.2/x86_64",
                    "sle-module-web-scripting/15.2/x86_64",
                    "sle-module-transactional-server/15.2/x86_64",
                ],
            )

    def test_list_extensions(self):
        """
        Test suseconnect.list_extensions without parameters
        """
        result = {
            "retcode": 0,
            "stdout": "Activate with: SUSEConnect -p sle-ha/15.2/x86_64",
        }
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(suseconnect.list_extensions(), ["sle-ha/15.2/x86_64"])
            salt_mock["cmd.run_all"].assert_called_with(
                ["SUSEConnect", "--list-extensions"]
            )

    def test_list_extensions_params(self):
        """
        Test suseconnect.list_extensions with parameters
        """
        result = {
            "retcode": 0,
            "stdout": "Activate with: SUSEConnect -p sle-ha/15.2/x86_64",
        }
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(
                suseconnect.list_extensions(url="https://scc.suse.com", root="/mnt"),
                ["sle-ha/15.2/x86_64"],
            )
            salt_mock["cmd.run_all"].assert_called_with(
                [
                    "SUSEConnect",
                    "--list-extensions",
                    "--url",
                    "https://scc.suse.com",
                    "--root",
                    "/mnt",
                ]
            )

    def test_list_extensions_error(self):
        """
        Test suseconnect.list_extensions error
        """
        result = {
            "retcode": 1,
            "stdout": "To list extensions, you must first register " "the base product",
            "stderr": "",
        }
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                suseconnect.list_extensions()

    def test_cleanup(self):
        """
        Test suseconnect.cleanup without parameters
        """
        result = {"retcode": 0, "stdout": "Service has been removed"}
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(suseconnect.cleanup(), "Service has been removed")
            salt_mock["cmd.run_all"].assert_called_with(["SUSEConnect", "--cleanup"])

    def test_cleanup_params(self):
        """
        Test suseconnect.cleanup with parameters
        """
        result = {"retcode": 0, "stdout": "Service has been removed"}
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(
                suseconnect.cleanup(root="/mnt"), "Service has been removed"
            )
            salt_mock["cmd.run_all"].assert_called_with(
                ["SUSEConnect", "--cleanup", "--root", "/mnt"]
            )

    def test_cleanup_error(self):
        """
        Test suseconnect.cleanup error
        """
        result = {"retcode": 1, "stdout": "some error", "stderr": ""}
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                suseconnect.cleanup()

    def test_rollback(self):
        """
        Test suseconnect.rollback without parameters
        """
        result = {
            "retcode": 0,
            "stdout": "Starting to sync system product activations",
        }
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(
                suseconnect.rollback(), "Starting to sync system product activations"
            )
            salt_mock["cmd.run_all"].assert_called_with(["SUSEConnect", "--rollback"])

    def test_rollback_params(self):
        """
        Test suseconnect.rollback with parameters
        """
        result = {
            "retcode": 0,
            "stdout": "Starting to sync system product activations",
        }
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            self.assertEqual(
                suseconnect.rollback(url="https://scc.suse.com", root="/mnt"),
                "Starting to sync system product activations",
            )
            salt_mock["cmd.run_all"].assert_called_with(
                [
                    "SUSEConnect",
                    "--rollback",
                    "--url",
                    "https://scc.suse.com",
                    "--root",
                    "/mnt",
                ]
            )

    def test_rollback_error(self):
        """
        Test suseconnect.rollback error
        """
        result = {"retcode": 1, "stdout": "some error", "stderr": ""}
        salt_mock = {
            "cmd.run_all": MagicMock(return_value=result),
        }
        with patch.dict(suseconnect.__salt__, salt_mock):
            with self.assertRaises(CommandExecutionError):
                suseconnect.rollback()
