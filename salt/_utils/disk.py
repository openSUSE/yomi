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

import re


class ParseException(Exception):
    pass


def units(value, default="MB"):
    """
    Split a value expressed (optionally) with units.

    Returns the tuple (value, unit)
    """
    valid_units = (
        "s",
        "B",
        "kB",
        "MB",
        "MiB",
        "GB",
        "GiB",
        "TB",
        "TiB",
        "%",
        "cyl",
        "chs",
        "compact",
    )
    match = re.search(r"^([\d.]+)(\D*)$", str(value))
    if match:
        value, unit = match.groups()
        unit = unit if unit else default
        if unit in valid_units:
            return (float(value), unit)
        else:
            raise ParseException("{} not recognized as a valid unit".format(unit))
    raise ParseException("{} cannot be parsed".format(value))
