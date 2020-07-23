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

import glob
import os.path


def __secure_boot():
    """Detect if secure-boot is enabled."""
    enabled = False
    sboot = glob.glob("/sys/firmware/efi/vars/SecureBoot-*/data")
    if len(sboot) == 1:
        enabled = open(sboot[0], "rb").read()[-1:] == b"\x01"
    return enabled


def uefi():
    """Populate UEFI grains."""
    grains = {
        "efi": os.path.exists("/sys/firmware/efi/systab"),
        "efi-secure-boot": __secure_boot(),
    }

    return grains
