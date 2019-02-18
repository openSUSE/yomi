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

from salt.exceptions import SaltInvocationError

import lp


LOG = logging.getLogger(__name__)

__virtualname__ = 'pplan'


# Define not exported variables from Salt, so this can be imported as
# a normal module
try:
    __grains__
    __opts__
    __pillars__
    __salt__
    __states__
    __utils__
except NameError:
    __grains__ = {}
    __opts__ = {}
    __pillars__ = {}
    __salt__ = {}
    __states__ = {}
    __utils__ = {}


PENALIZATION = {
    # Penalization for wasted space remaining in the device
    'free': 1,

    # Default penalizations
    'minimum_recommendation_size': 5,
    'maximum_recommendation_size': 2,
    'decrement_current_partition_size': 10,
    'increment_current_partition_size': 10,

    # /
    'root_minimum_recommendation_size': 5,
    'root_maximum_recommendation_size': 2,
    'root_decrement_current_partition_size': 10,
    'root_increment_current_partition_size': 10,

    # /home
    'home_minimum_recommendation_size': 5,
    'home_maximum_recommendation_size': 2,
    'home_decrement_current_partition_size': 10,
    'home_increment_current_partition_size': 10,

    # /var
    'var_minimum_recommendation_size': 5,
    'var_maximum_recommendation_size': 2,
    'var_decrement_current_partition_size': 10,
    'var_increment_current_partition_size': 10,
}

FREE = 'free'
MIN = 'minimum_recommendation_size'
MAX = 'maximum_recommendation_size'
INC = 'decrement_current_partition_size'
DEC = 'increment_current_partition_size'


def _penalization(partition=None, section=FREE):
    '''Penalization for a partition.'''
    kind = '{}_{}'.format(partition, section)
    if kind in PENALIZATION:
        return PENALIZATION[kind]
    return PENALIZATION[section]


def plan(name, constraints, unit='MB', export=False):
    '''Analyze the current hardware and make a partition proposal.

    name
        Name of the root element of the dictionary

    constraints
        List of constraints for the partitions. Each element of the
        list will be a tuple with a name of partition, aminimum size
        (None if not required), and a maximum size (None if not
        required).

        Example: "[['swap', null, null], ['home', 524288, null]]"

    unit
        Unit where the sizes are expressed. Are the same valid units
        for the parted module

    export
        Export the partition proposal as a grains under the given name

    CLI Example:

    .. code-block:: bash

        salt '*' pplan.plan proposal "[['swap', null, null], ...]"

    '''
    if not constraints:
        raise SaltInvocationError('contraints parameter is required')

    hd_size = __salt__['status.diskusage']('/dev/sda')['/dev/sda']['total']
    # TODO(aplanas) We only work on MB
    hd_size /= 1024

    # TODO(aplanas) Fix the situation with swap.
    # Replace the None in the max position in the constraints with
    # hd_size.
    constraints = [(c[0], c[1], c[2] if c[2] else hd_size)
                   for c in constraints]

    # Generate the variables of our model:
    #   <part>_size, <part>_to_min_size, <part>_from_max_size
    variables = ['{}_{}'.format(constraint[0], suffix)
                 for constraint in constraints
                 for suffix in ('size', 'to_min_size', 'from_max_size')]
    model = lp.Model(variables)

    for constraint in constraints:
        part_size = '{}_size'.format(constraint[0])
        part_to_min_size = '{}_to_min_size'.format(constraint[0])
        part_from_max_size = '{}_from_max_size'.format(constraint[0])
        model_constraints = (
            # <part>_size >= MINIMUM_RECOMMENDATION_SIZE - <part>_to_min_size
            ({part_size: 1, part_to_min_size: 1}, lp.GTE, constraint[1]),
            # <part>_size <= MAXIMUM_RECOMMENDATION_SIZE + <part>_from_max_size
            ({part_size: 1, part_from_max_size: 1}, lp.LTE, constraint[2]),
        )
        for model_constraint in model_constraints:
            model.add_constraint_named(*model_constraint)

    # sum(<part>_size) <= HD_SIZE
    model_constraint = ({'{}_size'.format(c[0]): 1 for c in constraints},
                        lp.LTE, hd_size)
    model.add_constraint_named(*model_constraint)

    # Minimize: PENALIZATION_FREE * (HD_SIZE - Sum(<part>_size))
    #   + PENALIZATION_MINIMUM_RECOMMENDATION_SIZE * <part>_to_min_size
    #   + PENALIZATION_MAXIMUM_RECOMMENDATIOM_SIZE * <part>_from_max_size
    coefficients = {
        '{}_{}'.format(constraint[0], suffix): _penalization(
            partition=constraint[0],
            section={'to_min_size': MIN, 'from_max_size': MAX}[suffix])
        for constraint in constraints
        for suffix in ('to_min_size', 'from_max_size')
    }
    coefficients.update({
        '{}_size'.format(constraint[0]): -_penalization(section=FREE)
        for constraint in constraints
    })
    model.add_cost_function_named(lp.MINIMIZE, coefficients,
                                  _penalization(section=FREE) * hd_size)

    plan = {name: model.simplex()}
    if export:
        __salt__['grains.setvals'](plan)

    return plan
