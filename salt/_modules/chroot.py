# Copyright (c) 2018 SUSE LINUX GmbH, Nuernberg, Germany.

# This file is part of Salt-autoinstaller.

# Salt-autoinstaller is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Salt-autoinstaller is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Salt-autoinstaller.  If not, see <https://www.gnu.org/licenses/>.

'''
:maintainer:    Alberto Planas <aplanas@suse.com>
:maturity:      new
:depends:       None
:platform:      Linux
'''
from __future__ import absolute_import, print_function, unicode_literals
import logging
import os
import sys
import tempfile

from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

__virtualname__ = 'chroot'


# Define not exported variables from Salt, so this can be imported as
# a normal module
try:
    __context__
    __grains__
    __opts__
    __pillars__
    __salt__
    __states__
    __utils__
except NameError:
    __context__ = {}
    __grains__ = {}
    __opts__ = {}
    __pillars__ = {}
    __salt__ = {}
    __states__ = {}
    __utils__ = {}


def __virtual__():
    '''
    Chroot command is required.
    '''
    return __utils__['path.which']('chroot') is not None


def exist(name):
    '''
    Return True if the chroot environment is present.
    '''
    dev = os.path.join(name, 'dev')
    proc = os.path.join(name, 'proc')
    return all(os.path.isdir(i) for i in (name, dev, proc))


def create(name, minimal=False):
    '''
    Create a basic chroot environment.
    '''
    if not exist(name):
        dev = os.path.join(name, 'dev')
        proc = os.path.join(name, 'proc')
        return __salt__['cmd.retcode'](['mkdir', '-p', name, dev, proc]) == 0
    return True


def call(name, function, *args, **kwargs):
    '''
    Executes a Salt function inside a chroot environment.

    The chroot does not need to have Salt installed, but Python is
    required.

    name
        Path to the chroot environment

    function
        Salt execution module function

    CLI Example:

    .. code-block:: bash

        salt myminion chroot.call /chroot test.ping
    '''

    if not function:
        raise CommandExecutionError('Missing function parameter')

    if not exist(name):
        raise CommandExecutionError('Chroot environment not found')

    # Create a temporary directory inside the chroot where we can
    # untar salt-thin
    thin_dest_path = tempfile.mkdtemp(dir=name)
    thin_path = __utils__['thin.gen_thin'](
        __opts__['cachedir'],
        extra_mods=__salt__['config.option']('thin_extra_mods', ''),
        so_mods=__salt__['config.option']('thin_so_mods', '')
    )
    __salt__['archive.tar']('xzf', thin_path, dest=thin_dest_path)
    if stdout:
       __utils__['files.rm_rf'](thin_dest_path)
       return {'result': False, 'comment': stdout}

    chroot_path = os.path.join(os.path.sep,
                               os.path.relpath(thin_dest_path, name))
    try:
        salt_argv = [
            'python{}'.format(sys.version_info[0]),
            os.path.join(chroot_path, 'salt-call'),
            '--metadata',
            '--local',
            '--log-file', os.path.join(chroot_path, 'log'),
            '--cachedir', os.path.join(chroot_path, 'cache'),
            '--out', 'json',
            '-l', 'quiet',
            '--',
            function
        ] + list(args) + [
            '{}={}'.format(k, v) for (k, v) in kwargs.items()
            if not k.startswith('__')
        ]
        ret = __salt__['cmd.run_chroot'](name, [str(x) for x in salt_argv])
        if ret['retcode'] != 0:
            raise CommandExecutionError(ret['stderr'])

        # Process "real" result in stdout
        try:
            data = __utils__['json.find_json'](ret['stdout'])
            local = data.get('local', data)
            if isinstance(local, dict):
                if 'retcode' in local:
                    __context__['retcode'] = local['retcode']
            return local.get('return', data)
        except ValueError:
            return {
                'result': False,
                'comment': "Can't parse container command output"
            }
    finally:
        __utils__['files.rm_rf'](thin_dest_path)
