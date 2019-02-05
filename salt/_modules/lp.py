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

EQ = '='
LTE = '<='
GTE = '>='

MINIMIZE = '-'
MAXIMIZE = '+'


def _vec_scalar(vector, scalar):
    """Multiply a vector by an scalar."""
    return [v * scalar for v in vector]


def _vec_vec_scalar(vector_a, vector_b, scalar):
    """Linear combination of two vectors and a scalar."""
    return [a * scalar + b for a, b in zip(vector_a, vector_b)]


class Model:
    """Class that represent a linear programming problem."""

    def __init__(self, variables):
        """Create a model with named variables."""
        # All variables are bound and >= 0. We do not support
        # unbounded variables.
        self.variables = variables

        self._slack_variables = []
        self._constraints = []
        self._cost_function = None

        self._standard = []

    def add_constraint(self, coefficients, operator, free_term):
        """Add a constraint in non-standard form."""
        # We can express constraints in a general form as:
        #
        #   a_1 x_1 + a_2 x_2 + ... + a_n x_n <= b
        #
        # For this case the values are:
        #   * coefficients = [a_1, a_2, ..., a_n]
        #   * operator = '<='
        #   * free_term = b
        #
        assert len(coefficients) == self.variables, 'Coefficients length ' \
            'must match the number of variables'
        assert operator in (EQ, LTE, GTE), 'Operator not valid'
        self._constraints.append((coefficients, operator, free_term))

    def add_cost_function(self, action, coefficients, free_term):
        """Add a cost function in non-standard form."""
        # We can express a cost function as:
        #
        #   Miminize: z = c_1 x_1 + c_2 x_2 + ... + c_n x_n + z_0
        #
        # For this case the values are:
        #   * action = '-'
        #   * coefficients = [c_1, c_2, ..., c_n]
        #   * free_term = z_0
        #
        assert action in (MINIMIZE, MAXIMIZE), 'Action not valid'
        assert len(coefficients) == self.variables, 'Coefficients length ' \
            'must match the number of variables'
        self._cost_function = (action, coefficients, free_term)

    def covert_to_standard_form(self):
        """Convert constraints and cost function to standard form."""
        slack_vars = len(c for c in self._constraints if c[1] != EQ)
        standard = []
        slack_var_idx = 0
        for coefficients, operator, free_term in self._constraints:
            slack_coeff = [0] * slack_vars
            if operator == LTE:
                slack_coeff[slack_var_idx] = 1
            elif operator == GTE:
                slack_coeff[slack_var_idx] = -1
                slack_var_idx += 1
            standard.append(coefficients + slack_coeff + [free_term])

        # Adjust the cost function
        action, coefficients, free_term = self._cost_function
        slack_coeff = [0] * slack_vars
        if action == MAXIMIZE:
            coefficients = _vec_scalar(coefficients, -1)
        standard.append(coefficients + slack_coeff + [-free_term])


class Tableau:
    # To sumarize the steps of the simplex method, starting with the
    # problem in canonical form.
    #
    # 1. if all c_j >= 0, the minimum value of the objective function
    #    has been achieved.
    #
    # 2. If there exists an s such that c_s < 0 and a_{is} <= 0 for
    #    all i, the objective function is not bounded below.
    #
    # 3. Otherwise, pivot. To determine the pivot term:
    #
    #    (a) Pivot in any column with a negative c_j term. If there
    #    are several negative c_j's, pivoting in the column with the
    #    smallest c_j may reduce the total number of steps necessary
    #    to complete the problem. Assume that we pivot column s.
    #
    #    (b) To determine the row of the pivot of the pivot term, find
    #    that row, say row r, such that
    #
    #      b_r / a_{rs} = Min { b_i / a_{is}: a_{is} > 0 }
    #
    #    Notice that here only those ratios b_i / a_{is} with a_{is} >
    #    0 are considered. If the minimum of there ratios is attained
    #    in several rows, a simple rule such as choosing the row with
    #    the smallest index can be used to determine the pivoting row.
    #
    # 4. After pivoting, the problem remains in canonical form at a
    #    different basic feasible solution. Now return to step 1.
    #
    # If the problem contains a degenerate b.f.s., proceed as above.

    def __init__(self, n, m):
        self.n = n
        self.m = m

        self._basic_variables = []
        self._tableau = []

    def add_constraint(self, constraint, basic_variable):
        """Add a contraint into the tableau."""
        assert len(constraint) == self.n + 1, 'Wrong size for the constraint'
        assert basic_variable not in self._basic_variables, \
            'Basic variable is already registered'
        assert len(self._basic_variables) == len(self._tableau) \
            and len(self._tableau) < self.m, 'Too many constraints registered'

        self._basic_variables.append(basic_variable)
        self._tableau.append(constraint)

    def add_cost_function(self, cost_function):
        """Add the const function in the tableau."""
        assert len(cost_function) == self.n + 1, \
            'Wrong size for the cost function'
        assert len(self._basic_variables) == len(self._tableau) \
            and len(self._tableau) == self.m, 'Too few constraints registered'

        self._tableau.append(cost_function)

    def is_canonical(self):
        """Check if the linear programing is in canonical form."""
        return True

    def simplex(self):
        """Resolve the constraints via the simplex algorithm."""
        while not self.is_minimum():
            column = self._get_pivoting_column()
            row = self._get_pivoting_row(column)
            self._pivote(row, column)
            self._basic_variables[row] = column

    def is_minimum(self):
        """Check if the cost function is already minimized."""
        return all(c >= 0 for c in self._tableau[-1][:-1])

    def constraints(self):
        """Return the constraints in the tableau."""
        return self._tableau[:-1]

    def cost_function(self):
        """Return the cost function in the tableau."""
        return self._tableau[-1]

    def _is_bound(self):
        """Check if the cost function is bounded."""
        candidates_idx = [i for i, c in enumerate(self.cost_function()[:-1])
                          if c < 0]
        return all(all(row[i] >= 0 for row in self.constraints())
                   for i in candidates_idx)

    def _get_pivoting_column(self):
        """Returm the column number where we can pivot."""
        candidates = [(i, c) for i, c in enumerate(self.cost_function()[:-1])
                      if c < 0]
        assert candidates, 'Cost function already minimal.'
        return min(candidates, key=lambda x: x[1])[0]

    def _get_pivoting_row(self, column):
        """Return the row number where we can pivot."""
        candidates = [(i, row[-1] / row[column])
                      for i, row in enumerate(self.constraints())
                      if row[column] > 0]
        # TODO(aplanas): Not sure that this is the case
        assert candidates, 'Cost function not bounded.'
        return min(candidates, key=lambda x: x[1])[0]

    def _scalar(self, row, value):
        """Scalar multiplication of a row and a value."""
        self._tableau[row] = _vec_scalar(self._tableau[row], value)

    def _linear(self, row_a, row_b, value):
        """Linear combination of two rows and a value."""
        self._tableau[row_b] = _vec_vec_scalar(self._tableau[row_a],
                                               self._tableau[row_a], value)

    def _pivote(self, row, column):
        """Pivote the tableau in (row, column)."""
        # Normalize the row
        self._scalar(row, 1 / self._tableau[row][column])
        for row_b in range(len(self._tableau)):
            if row != row_b:
                self._linear(row, row_b, -self._tableau[row_b][column])


if __name__ == 'main':
    pass
