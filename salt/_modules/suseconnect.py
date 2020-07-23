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
import json
import logging
import re

import salt.utils.path
from salt.exceptions import CommandExecutionError

LOG = logging.getLogger(__name__)

__virtualname__ = "suseconnect"


def __virtual__():
    """
    Only load the module if SUSEConnect is installed
    """
    if not salt.utils.path.which("SUSEConnect"):
        return (False, "SUSEConnect is not installed.")
    return __virtualname__


# Define not exported variables from Salt, so this can be imported as
# a normal module
try:
    __salt__
except NameError:
    __salt__ = {}


def _cmd(cmd):
    """Utility function to run commands."""
    result = __salt__["cmd.run_all"](cmd)
    if result["retcode"]:
        raise CommandExecutionError(result["stdout"] + result["stderr"])
    return result["stdout"]


def register(regcode, product=None, email=None, url=None, root=None):
    """
    .. versionadded:: TBD

    Register SUSE Linux Enterprise installation with the SUSE Customer
    Center

    regcode
       Subscription registration code for the product to be
       registered. Relates that product to the specified subscription,
       and enalbes software repositories for that product.

    product
       Specify a product for activation/deactivation. Only one product
       can be processed at a time. Defaults to the base SUSE Linux
       Enterprose product on this system.
       Format: <name>/<version>/<architecture>

    email
       Email address for product registration

    url
       URL for the registration server (will be saved for the next
       use) (e.g. https://scc.suse.com)

    root
       Path to the root folder, uses the same parameter for zypper

    CLI Example:

    .. code-block:: bash

       salt '*' suseconnect.register xxxx-yyy-zzzz
       salt '*' suseconnect.register xxxx-yyy-zzzz product='sle-ha/15.2/x86_64'

    """
    cmd = ["SUSEConnect", "--regcode", regcode]

    parameters = [("product", product), ("email", email), ("url", url), ("root", root)]

    for parameter, value in parameters:
        if value:
            cmd.extend(["--{}".format(parameter), str(value)])

    return _cmd(cmd)


def deregister(product=None, url=None, root=None):
    """
    .. versionadded:: TBD

    De-register the system and base product, or in cojuntion with
    'product', a single extension, and removes all its services
    installed by SUSEConnect. After de-registration the system no
    longer consumes a subscription slot in SCC.

    product
       Specify a product for activation/deactivation. Only one product
       can be processed at a time. Defaults to the base SUSE Linux
       Enterprose product on this system.
       Format: <name>/<version>/<architecture>

    url
       URL for the registration server (will be saved for the next
       use) (e.g. https://scc.suse.com)

    root
       Path to the root folder, uses the same parameter for zypper

    CLI Example:

    .. code-block:: bash

       salt '*' suseconnect.deregister
       salt '*' suseconnect.deregister product='sle-ha/15.2/x86_64'

    """
    cmd = ["SUSEConnect", "--de-register"]

    parameters = [("product", product), ("url", url), ("root", root)]

    for parameter, value in parameters:
        if value:
            cmd.extend(["--{}".format(parameter), str(value)])

    return _cmd(cmd)


def status(root=None):
    """
    .. versionadded:: TBD

    Get current system registation status.

    root
       Path to the root folder, uses the same parameter for zypper

    CLI Example:

    .. code-block:: bash

       salt '*' suseconnect.status

    """
    cmd = ["SUSEConnect", "--status"]

    parameters = [("root", root)]

    for parameter, value in parameters:
        if value:
            cmd.extend(["--{}".format(parameter), str(value)])

    return json.loads(_cmd(cmd))


def _parse_list_extensions(output):
    """Parse the output of list-extensions result"""
    # We can extract the indentation using this regex:
    #   r'( {4,}).*\s([-\w]+/[-\w\.]+/[-\w]+).*'
    return re.findall(r"\s([-\w]+/[-\w\.]+/[-\w]+)", output)


def list_extensions(url=None, root=None):
    """
    .. versionadded:: TBD

    List all extensions and modules avaiable for installation on this
    system.

    url
       URL for the registration server (will be saved for the next
       use) (e.g. https://scc.suse.com)

    root
       Path to the root folder, uses the same parameter for zypper

    CLI Example:

    .. code-block:: bash

       salt '*' suseconnect.list-extensions
       salt '*' suseconnect.list-extensions url=https://scc.suse.com

    """
    cmd = ["SUSEConnect", "--list-extensions"]

    parameters = [("url", url), ("root", root)]

    for parameter, value in parameters:
        if value:
            cmd.extend(["--{}".format(parameter), str(value)])

    # TODO(aplanas) Implement a better parser
    return _parse_list_extensions(_cmd(cmd))


def cleanup(root=None):
    """
    .. versionadded:: TBD

    Remove olf system credential and all zypper services installed by
    SUSEConnect

    root
       Path to the root folder, uses the same parameter for zypper

    CLI Example:

    .. code-block:: bash

       salt '*' suseconnect.cleanup

    """
    cmd = ["SUSEConnect", "--cleanup"]

    parameters = [("root", root)]

    for parameter, value in parameters:
        if value:
            cmd.extend(["--{}".format(parameter), str(value)])

    return _cmd(cmd)


def rollback(url=None, root=None):
    """
    .. versionadded:: TBD

    Revert the registration state in case of a failed migration.

    url
       URL for the registration server (will be saved for the next
       use) (e.g. https://scc.suse.com)

    root
       Path to the root folder, uses the same parameter for zypper

    CLI Example:

    .. code-block:: bash

       salt '*' suseconnect.rollback
       salt '*' suseconnect.rollback url=https://scc.suse.com

    """
    cmd = ["SUSEConnect", "--rollback"]

    parameters = [("url", url), ("root", root)]

    for parameter, value in parameters:
        if value:
            cmd.extend(["--{}".format(parameter), str(value)])

    return _cmd(cmd)
