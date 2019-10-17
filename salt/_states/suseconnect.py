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
import re

from salt.exceptions import CommandExecutionError

LOG = logging.getLogger(__name__)

__virtualname__ = 'suseconnect'

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
    SUSEConnect module is required
    '''
    return 'suseconnect.register' in __salt__


def _status(root):
    '''
    Return the list of resitered modules and subscriptions
    '''
    status = __salt__['suseconnect.status'](root=root)
    registered = [
        '{}/{}/{}'.format(i['identifier'], i['version'], i['arch'])
        for i in status if i['status'] == 'Registered'
    ]
    subscriptions = [
        '{}/{}/{}'.format(i['identifier'], i['version'], i['arch'])
        for i in status if i.get('subscription_status') == 'ACTIVE'
    ]
    return registered, subscriptions


def _is_registered(product, root):
    '''
    Check if a product is registered
    '''
    # If the user provides a product, and the product is registered,
    # or if the user do not provide a product name, but some
    # subscription is active, we consider that there is nothing else
    # to do.
    registered, subscriptions = _status(root)
    if (product and product in registered) or (not product and subscriptions):
        return True
    return False


def registered(name, regcode, product=None, email=None, url=None, root=None):
    '''
    .. versionadded:: TBD

    Register SUSE Linux Enterprise installation with the SUSE Customer
    Center

    name
       If follows the product name rule, will be the name of the
       product.

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

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    if not product and re.match(r'[-\w]+/[-\w\.]+/[-\w]+', name):
        product = name
    name = product if product else 'default'

    if _is_registered(product, root):
        ret['result'] = True
        ret['comment'].append('Product or module {} already registered'.format(
            name))
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'].append('Product or module {} would be '
                              'registered'.format(name))
        ret['changes'][name] = True
        return ret

    try:
        __salt__['suseconnect.register'](regcode, product=product,
                                         email=email, url=url,
                                         root=root)
    except CommandExecutionError as e:
        ret['comment'].append('Error registering {}: {}'.format(name, e))
        return ret

    ret['changes'][name] = True

    if _is_registered(product, root):
        ret['result'] = True
        ret['comment'].append('Product or module {} registered'.format(name))
    else:
        ret['comment'].append('Product or module {} failed to register'.format(
            name))

    return ret


def deregistered(name, product=None, url=None, root=None):
    '''
    .. versionadded:: TBD

    De-register the system and base product, or in cojuntion with
    'product', a single extension, and removes all its services
    installed by SUSEConnect. After de-registration the system no
    longer consumes a subscription slot in SCC.

    name
       If follows the product name rule, will be the name of the
       product.

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

    '''
    ret = {
        'name': name,
        'result': False,
        'changes': {},
        'comment': [],
    }

    if not product and re.match(r'[-\w]+/[-\w\.]+/[-\w]+', name):
        product = name
    name = product if product else 'default'

    if not _is_registered(product, root):
        ret['result'] = True
        ret['comment'].append('Product or module {} already '
                              'deregistered'.format(name))
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'].append('Product or module {} would be '
                              'deregistered'.format(name))
        ret['changes'][name] = True
        return ret

    try:
        __salt__['suseconnect.deregister'](product=product, url=url,
                                           root=root)
    except CommandExecutionError as e:
        ret['comment'].append('Error deregistering {}: {}'.format(name, e))
        return ret

    ret['changes'][name] = True

    if not _is_registered(product, root):
        ret['result'] = True
        ret['comment'].append('Product or module {} deregistered'.format(name))
    else:
        ret['comment'].append('Product or module {} failed to '
                              'deregister'.format(name))

    return ret
