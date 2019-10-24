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

'''
:maintainer:    Alberto Planas <aplanas@suse.com>
:maturity:      new
:depends:       None
:platform:      Linux
'''
from __future__ import absolute_import, print_function, unicode_literals
import logging
import os
import os.path
import tempfile
import urllib.parse

LOG = logging.getLogger(__name__)

__virtualname__ = 'images'

# Define not exported variables from Salt, so this can be imported as
# a normal module
try:
    __opts__
    __salt__
    __utils__
except NameError:
    __opts__ = {}
    __salt__ = {}
    __utils__ = {}


# Copied from `images` execution module, as we cannot easly import it
VALID_SCHEME = ('dict', 'file', 'ftp', 'ftps', 'gopher', 'http',
                'https', 'imap', 'imaps', 'ldap', 'ldaps', 'pop3',
                'pop3s', 'rtmp', 'rtsp', 'scp', 'sftp', 'smb', 'smbs',
                'smtp', 'smtps', 'telnet', 'tftp')
VALID_COMPRESSIONS = ('gz', 'bz2', 'xz')
VALID_CHECKSUMS = ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512')


def __virtual__():
    '''Images depends on images.dump module'''
    return 'images.dump' in __salt__


def _mount(device):
    '''Mount the device in a temporary place'''
    dest = tempfile.mkdtemp()
    res = __salt__['mount.mount'](name=dest, device=device)
    if res is not True:
        return None
    return dest


def _umount(path):
    '''Umount and clean the temporary place'''
    __salt__['mount.umount'](path)
    __utils__['files.rm_rf'](path)


def _checksum_path(root):
    '''Return the path where we will store the last checksum'''
    return os.path.join(root, __opts__['cachedir'][1:], 'images')


def _read_current_checksum(device, checksum_type):
    '''Return the checksum of the current image, if any'''
    checksum = None
    mnt = _mount(device)
    if not mnt:
        return None

    checksum_file = os.path.join(_checksum_path(mnt),
                                 'checksum.{}'.format(checksum_type))
    try:
        checksum = open(checksum_file).read()
        LOG.info('Checksum file %s content: %s', checksum_file, checksum)
    except Exception:
        # If the file cannot be read, we expect that the image needs
        # to be re-applied eventually
        LOG.info('Checksum file %s not found', checksum_file)

    _umount(mnt)
    return checksum


def _save_current_checksum(device, checksum_type, checksum):
    '''Save the checksum of the current image'''
    result = False
    mnt = _mount(device)
    if not mnt:
        return result

    checksum_path = _checksum_path(mnt)
    os.makedirs(checksum_path, exist_ok=True)
    checksum_file = os.path.join(checksum_path,
                                 'checksum.{}'.format(checksum_type))
    try:
        checksum_file = open(checksum_file, 'w')
        checksum_file.write(checksum)
        checksum_file.close()
        result = True
        LOG.info('Created checksum file %s content: %s', checksum_file,
                 checksum)
    except Exception:
        LOG.error('Error writing checksum file %s', checksum_file)

    _umount(mnt)
    return result


def _is_dump_needed(device, checksum_type, checksum):
    return True


def dumped(name, device, checksum_type=None, checksum=None, **kwargs):
    '''
    Copy an image in the device.

    name
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

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    scheme, _, path, *_ = urllib.parse.urlparse(name)
    if scheme not in VALID_SCHEME:
        ret['comment'].append('Protocol not valid for URL')
        return ret

    # We cannot validate the compression extension, as we can have
    # non-restricted file names, like '/my-image.ext3' or
    # 'other-image.raw'.

    if checksum_type and checksum_type not in VALID_CHECKSUMS:
        ret['comment'].append('Checksum type not valid')
        return ret

    if not checksum_type and checksum:
        ret['comment'].append('Checksum type not provided')
        return ret

    if checksum_type and not checksum:
        checksum = __salt__['images.fetch_checksum'](name, checksum_type,
                                                     **kwargs)
        if not checksum:
            ret['comment'].append('Checksum no found')
            return ret

    if checksum_type:
        current_checksum = _read_current_checksum(device, checksum_type)

    if __opts__['test']:
        ret['result'] = None
        if checksum_type:
            ret['changes']['image'] = current_checksum != checksum
            ret['changes']['checksum cache'] = ret['changes']['image']
        return ret

    if checksum_type and current_checksum != checksum:
        result = __salt__['images.dump'](name, device, checksum_type,
                                         checksum, **kwargs)
        if result != checksum:
            ret['comment'].append('Failed writing the image')
            return ret
        else:
            ret['changes']['image'] = True

        saved = _save_current_checksum(device, checksum_type, checksum)
        if not saved:
            ret['comment'].append('Checksum failed to be saved in the cache')
            return ret
        else:
            ret['changes']['checksum cache'] = True

    ret['result'] = True
    return ret
