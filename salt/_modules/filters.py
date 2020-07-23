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

"""
:maintainer:    Alberto Planas <aplanas@suse.com>
:maturity:      new
:depends:       None
:platform:      Linux
"""
from __future__ import absolute_import, print_function, unicode_literals
import logging


LOG = logging.getLogger(__name__)

__virtualname__ = "filters"


# Define not exported variables from Salt, so this can be imported as
# a normal module
try:
    __pillar__
except NameError:
    __pillar__ = {}


def is_lvm(device):
    """Detect if a device name comes from a LVM volume."""
    devices = ["/dev/{}/".format(i) for i in __pillar__.get("lvm", {})]
    devices.extend(("/dev/mapper/", "/dev/dm-"))
    return device.startswith(tuple(devices))


def is_raid(device):
    """Detect if a device name comes from a RAID array."""
    return device.startswith("/dev/md")


def is_not_raid(device):
    """Detect if a device name comes from a RAID array."""
    return not is_raid(device)
