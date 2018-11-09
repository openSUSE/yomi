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

from salt.exceptions import CommandExecutionError
import salt.utils.json as json

log = logging.getLogger(__name__)

__virtualname__ = 'freezer'


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
    Freezer is based on top of the pkg module.
    '''
    return 'pkg.list_pkgs' in __salt__


def _states_path():
    '''
    Return the path where we will store the states.
    '''
    return os.path.join(__opts__['cachedir'], 'freezer')


def _paths(name=None):
    '''
    Return the full path for the packages and repository freezer
    files.

    '''
    name = 'freezer' if not name else name
    states_path = _states_path()
    return (
        os.path.join(states_path, '{}-pkgs.yml'.format(name)),
        os.path.join(states_path, '{}-reps.yml'.format(name)),
    )


def isfrozen(name=None):
    '''
    Return True if there is already a frozen state.

    A frozen state is merely a list of packages (including the
    version) in a specific time. This information can be used to
    compare with the current list of packages, and revert the
    installation of some extra packages that are in the system.

    name
        Name of the frozen state. Optional.

    CLI Example:

    .. code-block:: bash

        salt '*' freezer.isfrozen

    '''
    name = 'freezer' if not name else name
    return all(os.path.isfile(i) for i in _paths(name))


def list():
    '''
    Return the list of frozen states.

    CLI Example:

    .. code-block:: bash

        salt '*' freezer.list

    '''
    ret = []
    states_path = _states_path()
    if not os.path.isdir(states_path):
        return ret

    for state in os.listdir(states_path):
        if state.endswith(('-pkgs.yml', '-reps.yml')):
            # Remove the suffix, as both share the same size
            ret.append(state[:-9])
    return sorted(set(ret))


def freeze(name=None, force=False, **kwargs):
    '''
    Save the list of package and repos in a freeze file.

    As this module is build on top of the pkg module, the user can
    send extra attributes to the underlining pkg module via kwargs.

    name
        Name of the frozen state. Optional.

    force
        If true, overwrite the state. Optional.

    CLI Example:

    .. code-block:: bash

        salt '*' freezer.freeze
        salt '*' freezer.freeze force=True root=/chroot

    '''
    states_path = _states_path()
    ret = __salt__['cmd.retcode'](['mkdir', '-p', states_path])
    if ret:
        msg = 'Error when trying to create the freezer ' \
            'storage: {}'.format(states_path)
        log.error(msg)
        raise CommandExecutionError(msg)

    if isfrozen(name) and not force:
        raise CommandExecutionError('The state is already present. Use '
                                    'force parameter to overwrite.')
    safe_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('__')}
    pkgs = __salt__['pkg.list_pkgs'](**safe_kwargs)
    repos = __salt__['pkg.list_repos'](**safe_kwargs)
    for name, content in zip(_paths(name), (pkgs, repos)):
        with open(name, 'w') as fp:
            json.dump(content, fp)
    return True


def recover(name=None, full=False, **kwargs):
    '''
    Make sure that the system contains the packages and repos from a
    frozen state.

    Read the list of packages and repositories from the freeze file,
    and compare it with the current list of packages and repos. If
    there is any difference, all the missing packages are repos will
    be installed, and all the extra packages and repos will be
    removed.

    As this module is build on top of the pkg module, the user can
    send extra attributes to the underlining pkg module via kwargs.

    name
        Name of the frozen state. Optional.

    remove
        If true, Koverwrite the state. Optional.

    CLI Example:

    .. code-block:: bash

        salt '*' freezer.recover
        salt '*' freezer.recover remove=True root=/chroot

    '''
    if not isfrozen(name):
        raise CommandExecutionError('Frozen state not found.')

    frozen_pkgs = {}
    frozen_repos = {}
    for name, content in zip(_paths(name), (frozen_pkgs, frozen_repos)):
        with open(name) as fp:
            content.update(json.load(fp))

    # The ordering of removing or adding packages and repos can be
    # relevant, as maybe some missing package comes from a repo that
    # is also missing, so it cannot be installed. But can also happend
    # that a missing package comes from a repo that is present, but
    # will be removed.
    #
    # So the proposed order is;
    #   - Add missing repos
    #   - Add missing packages
    #   - Remove extra packages
    #   - Remove extra repos

    safe_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('__')}

    # Note that we expect that the information stored in list_XXX
    # match with the mod_XXX counterpart. If this is not the case the
    # recovery will be partial.

    res = {
        'pkgs': {'add': [], 'remove': []},
        'repos': {'add': [], 'remove': []},
        'comment': [],
    }

    # Add missing repositories
    repos = __salt__['pkg.list_repos'](**safe_kwargs)
    missing_repos = set(frozen_repos) - set(repos)
    for repo in missing_repos:
        try:
            __salt__['pkg.mod_repo'](repo=repo, **frozen_repos[repo],
                                     **safe_kwargs)
            res['repos']['add'].append(repo)
            log.info('Added missing repository {}'.format(repo))
        except Exception as e:
            msg = 'Error adding {} repository: {}'.format(repo, e)
            log.error(msg)
            res['comment'].append(msg)

    # Add missing packages
    # NOTE(aplanas) we can remove the `for` using `pkgs`. This will
    # improve performance, but I want to have a more detalied report
    # of what packages are installed or failled.
    pkgs = __salt__['pkg.list_pkgs'](**safe_kwargs)
    missing_pkgs = set(frozen_pkgs) - set(pkgs)
    for pkg in missing_pkgs:
        try:
            __salt__['pkg.install'](name=pkg, **safe_kwargs)
            res['pkgs']['add'].append(pkg)
            log.info('Added missing package {}'.format(pkg))
        except Exception as e:
            msg = 'Error adding {} package: {}'.format(pkg, e)
            log.error(msg)
            res['comment'].append(msg)

    # Remove extra packages
    pkgs = __salt__['pkg.list_pkgs'](**safe_kwargs)
    extra_pkgs = set(pkgs) - set(frozen_pkgs)
    for pkg in extra_pkgs:
        try:
            __salt__['pkg.remove'](name=pkg, **safe_kwargs)
            res['pkgs']['remove'].append(pkg)
            log.info('Removed extra package {}'.format(pkg))
        except Exception as e:
            msg = 'Error removing {} package: {}'.format(pkg, e)
            log.error(msg)
            res['comment'].append(msg)

    # Remove extra repositories
    repos = __salt__['pkg.list_repos'](**safe_kwargs)
    extra_repos = set(repos) - set(frozen_repos)
    for repo in extra_repos:
        try:
            __salt__['pkg.del_repo'](repo, **safe_kwargs)
            res['repos']['remove'].append(repo)
            log.info('Removed extra repository {}'.format(repo))
        except Exception as e:
            msg = 'Error removing {} repository: {}'.format(repo, e)
            log.error(msg)
            res['comment'].append(msg)

    return res
