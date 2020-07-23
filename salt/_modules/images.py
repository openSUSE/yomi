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
import pathlib
import urllib.parse

from salt.exceptions import SaltInvocationError, CommandExecutionError
import salt.utils.args

LOG = logging.getLogger(__name__)

__virtualname__ = "images"

# Define not exported variables from Salt, so this can be imported as
# a normal module
try:
    __salt__
except NameError:
    __salt__ = {}


VALID_SCHEME = (
    "dict",
    "file",
    "ftp",
    "ftps",
    "gopher",
    "http",
    "https",
    "imap",
    "imaps",
    "ldap",
    "ldaps",
    "pop3",
    "pop3s",
    "rtmp",
    "rtsp",
    "scp",
    "sftp",
    "smb",
    "smbs",
    "smtp",
    "smtps",
    "telnet",
    "tftp",
)
VALID_COMPRESSIONS = ("gz", "bz2", "xz")
VALID_CHECKSUMS = ("md5", "sha1", "sha224", "sha256", "sha384", "sha512")


def _checksum_url(url, checksum_type):
    """Generate the URL for the checksum"""
    url_elements = urllib.parse.urlparse(url)
    path = url_elements.path
    suffix = pathlib.Path(path).suffix
    new_suffix = ".{}".format(checksum_type)
    if suffix[1:] in VALID_COMPRESSIONS:
        path = pathlib.Path(path).with_suffix(new_suffix)
    else:
        path = pathlib.Path(path).with_suffix(suffix + new_suffix)
    return urllib.parse.urlunparse(url_elements._replace(path=str(path)))


def _curl_cmd(url, **kwargs):
    """Return curl commmand line"""
    cmd = ["curl"]
    for key, value in salt.utils.args.clean_kwargs(**kwargs).items():
        if len(key) == 1:
            cmd.append("-{}".format(key))
        else:
            cmd.append("--{}".format(key))
        if value is not None:
            cmd.append(value)
    cmd.append(url)
    return cmd


def _fetch_file(url, **kwargs):
    """Get a file and return the content"""
    params = {
        "silent": None,
        "location": None,
    }
    params.update(kwargs)
    return __salt__["cmd.run_stdout"](_curl_cmd(url, **params))


def _find_filesystem(device):
    """Use lsblk to find the filesystem of a partition."""
    cmd = ["lsblk", "--noheadings", "--output", "FSTYPE", device]
    return __salt__["cmd.run_stdout"](cmd)


def fetch_checksum(url, checksum_type, **kwargs):
    """
    Fecht the checksum from an image URL

    url
        URL of the image. The protocol scheme needs to be available in
        curl. For example: http, https, scp, sftp, tftp or ftp.

        The image can be compressed, and the supported extensions are:
        gz, bz2 and xz

    checksum_type
        The type of checksum used to validate the image, possible
        values are 'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'.

    Other paramaters send via kwargs will be used during the call for
    curl.

    CLI Example:

    .. code-block:: bash

        salt '*' images.fetch_checksum https://my.url/JeOS.xz checksum_type=md5

    """

    checksum_url = _checksum_url(url, checksum_type)
    checksum = _fetch_file(checksum_url, **kwargs)
    if not checksum:
        raise CommandExecutionError(
            "Checksum file not found in {}".format(checksum_url)
        )
    checksum = checksum.split()[0]
    LOG.info("Checksum for the image {}".format(checksum))
    return checksum


def dump(url, device, checksum_type=None, checksum=None, **kwargs):
    """Download an image and copy it into a device

    url
        URL of the image. The protocol scheme needs to be available in
        curl. For example: http, https, scp, sftp, tftp or ftp.

        The image can be compressed, and the supported extensions are:
        gz, bz2 and xz

    device
        The device or partition where the image will be copied.

    checksum_type
        The type of checksum used to validate the image, possible
        values are 'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'.

    checksum
        The checksum value. If omitted but a `checksum_type` was set,
        it will try to download the checksum file from the same URL,
        replacing the extension with the `checksum_type`

    Other paramaters send via kwargs will be used during the call for
    curl.

    If succeed it will return the real checksum of the image. If
    checksum_type is not specified, MD5 will be used.

    CLI Example:

    .. code-block:: bash

        salt '*' images.dump https://my.url/JeOS-btrfs.xz /dev/sda1
        salt '*' images.dump tftp://my.url/JeOS.xz /dev/sda1 checksum_type=md5

    """

    scheme, _, path, *_ = urllib.parse.urlparse(url)
    if scheme not in VALID_SCHEME:
        raise SaltInvocationError("Protocol not valid for URL")

    # We cannot validate the compression extension, as we can have
    # non-restricted file names, like '/my-image.ext3' or
    # 'other-image.raw'.

    if checksum_type and checksum_type not in VALID_CHECKSUMS:
        raise SaltInvocationError("Checksum type not valid")

    if not checksum_type and checksum:
        raise SaltInvocationError("Checksum type not provided")

    if checksum_type and not checksum:
        checksum = fetch_checksum(url, checksum_type, **kwargs)

    params = {
        "fail": None,
        "location": None,
        "silent": None,
    }
    params.update(kwargs)

    # If any element in the pipe fail, exit early
    cmd = ["set -eo pipefail", ";"]
    cmd.extend(_curl_cmd(url, **params))

    suffix = pathlib.Path(path).suffix[1:]
    if suffix in VALID_COMPRESSIONS:
        cmd.append("|")
        cmd.extend(
            {"gz": ["gunzip"], "bz2": ["bzip2", "-d"], "xz": ["xz", "-d"]}[suffix]
        )

    checksum_prg = "{}sum".format(checksum_type) if checksum_type else "md5sum"
    cmd.extend(["|", "tee", device, "|", checksum_prg])
    ret = __salt__["cmd.run_all"](" ".join(cmd), python_shell=True)
    if ret["retcode"]:
        raise CommandExecutionError(
            "Error while fetching image {}: {}".format(url, ret["stderr"])
        )

    new_checksum = ret["stdout"].split()[0]

    if checksum_type and checksum != new_checksum:
        raise CommandExecutionError(
            "Checksum mismatch. "
            "Expected {}, calculated {}".format(checksum, new_checksum)
        )

    filesystem = _find_filesystem(device)

    resize_cmd = {
        "ext2": "e2fsck -f -y {0}; resize2fs {0}".format(device),
        "ext3": "e2fsck -f -y {0}; resize2fs {0}".format(device),
        "ext4": "e2fsck -f -y {0}; resize2fs {0}".format(device),
        "btrfs": "mount {} /mnt; btrfs filesystem resize max /mnt;"
        " umount /mnt".format(device),
        "xfs": "mount {} /mnt; xfs_growfs /mnt; umount /mnt".format(device),
    }
    if filesystem not in resize_cmd:
        raise CommandExecutionError(
            "Filesystem {} cannot be resized.".format(filesystem)
        )

    ret = __salt__["cmd.run_all"](resize_cmd[filesystem], python_shell=True)
    if ret["retcode"]:
        raise CommandExecutionError(
            "Error while resizing the partition {}: {}".format(device, ret["stderr"])
        )

    __salt__["cmd.run"]("sync")

    return new_checksum
