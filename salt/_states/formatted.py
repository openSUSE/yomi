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

'''
:maintainer:    Alberto Planas <aplanas@suse.com>
:maturity:      new
:depends:       None
:platform:      Linux
'''
from __future__ import absolute_import, print_function, unicode_literals
import logging
import os.path

LOG = logging.getLogger(__name__)

__virtualname__ = 'formatted'


# Define not exported variables from Salt, so this can be imported as
# a normal module
try:
    __opts__
    __salt__
    __states__
except NameError:
    __opts__ = {}
    __salt__ = {}
    __states__ = {}


def __virtual__():
    '''
    Formatted can be considered as an extension to blockdev

    '''
    return 'blockdev.formatted' in __states__


def formatted(name, fs_type=u'ext4', force=False, **kwargs):
    '''
    Manage filesystems of partitions.

    name
        The name of the block device

    fs_type
        The filesystem it should be formatted as

    force
        Force mke2fs to create a filesystem, even if the specified
        device is not a partition on a block special device. This
        option is only enabled for ext and xfs filesystems

        This option is dangerous, use it with caution.

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    fs_type = 'swap' if fs_type == 'linux-swap' else fs_type
    if fs_type != 'swap':
        ret = __states__['blockdev.formatted'](name, fs_type, force, **kwargs)
        return ret

    if not os.path.exists(name):
        ret['comment'].append('{} does not exist'.format(name))
        return ret

    current_fs = _checkblk(name)

    if current_fs == 'swap':
        ret['result'] = True
        return ret
    elif __opts__['test']:
        ret['comment'].append('Changes to {} will be applied '.format(name))
        ret['result'] = None
        return ret

    cmd = ['mkswap']
    if force:
        cmd.append('-f')
    if kwargs.pop('check', False):
        cmd.append('-c')
    for parameter, argument in (('-p', 'pagesize'),
                                ('-L', 'label'),
                                ('-v', 'swapversion'),
                                ('-U', 'uuid')):
        if argument in kwargs:
            cmd.extend([parameter, kwargs.pop(argument)])
    cmd.append(name)

    __salt__['cmd.run'](cmd)

    current_fs = _checkblk(name)

    if current_fs == 'swap':
        ret['comment'].append(('{} has been formatted '
                               'with {}').format(name, fs_type))
        ret['changes'] = {'new': fs_type, 'old': current_fs}
        ret['result'] = True
    else:
        ret['comment'].append('Failed to format {}'.format(name))
        ret['result'] = False
    return ret


def _checkblk(name):
    '''
    Check if the blk exists and return its fstype if ok
    '''

    blk = __salt__['cmd.run']('blkid -o value -s TYPE {0}'.format(name),
                              ignore_retcode=True)
    return '' if not blk else blk
