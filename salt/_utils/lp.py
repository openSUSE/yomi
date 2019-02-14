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


def _vec_plus_vec(vector_a, vector_b):
    """Sum of two vectors."""
    return [a + b for a, b in zip(vector_a, vector_b)]


class Model:
    """Class that represent a linear programming problem."""

    def __init__(self, variables):
        """Create a model with named variables."""
        # All variables are bound and >= 0. We do not support
        # unbounded variables.
        self.variables = variables

        self._constraints = []
        self._cost_function = None

        self._slack_variables = []
        self._standard_constraints = []
        self._standard_cost_function = None

        self._canonical_constraints = []
        self._canonical_cost_function = None
        self._canonical_artificial_function = None

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
        assert len(coefficients) == len(self.variables), 'Coefficients  ' \
            'length must match the number of variables'
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
        assert len(coefficients) == len(self.variables), 'Coefficients  ' \
            'length must match the number of variables'
        self._cost_function = (action, coefficients, free_term)

    def _coeff(self, coefficients):
        """Translate a coefficients dictionary into a list."""
        coeff = [0] * len(self.variables)
        for idx, variable in enumerate(self.variables):
            coeff[idx] = coefficients.get(variable, 0)
        return coeff

    def add_constraint_named(self, coefficients, operator, free_term):
        """Add a constraint in non-standard form."""
        self.add_constraint(self._coeff(coefficients), operator, free_term)

    def add_cost_function_named(self, action, coefficients, free_term):
        """Add a cost function in non-standard form."""
        self.add_cost_function(action, self._coeff(coefficients), free_term)

    def simplex(self):
        """Resolve a linear programing model."""
        self._convert_to_standard_form()
        self._convert_to_canonical_form()
        tableau = self._build_tableau_canonical_form()
        tableau.simplex()
        tableau.drop_artificial()
        tableau.simplex()

        constraints = tableau.constraints()
        solution = {i: 0 for i in self.variables}
        for idx_cons, idx_var in enumerate(tableau._basic_variables):
            variable = self.variables[idx_var]
            solution[variable] = constraints[idx_cons][-1]
        return solution

    def _convert_to_standard_form(self):
        """Convert constraints and cost function to standard form."""
        slack_vars = len([c for c in self._constraints if c[1] != EQ])

        self._standard_constraints = []
        slack_var_idx = 0
        base_slack_var_idx = len(self.variables)
        for coefficients, operator, free_term in self._constraints:
            slack_coeff = [0] * slack_vars
            if operator in (LTE, GTE):
                slack_coeff[slack_var_idx] = 1 if operator == LTE else -1
                self._slack_variables.append(
                    base_slack_var_idx + slack_var_idx)
                slack_var_idx += 1
            self._standard_constraints.append(
                (coefficients + slack_coeff, free_term))

        # Adjust the cost function
        action, coefficients, free_term = self._cost_function
        slack_coeff = [0] * slack_vars
        if action == MAXIMIZE:
            coefficients = _vec_scalar(coefficients, -1)
        self._standard_cost_function = (coefficients + slack_coeff, -free_term)

    def _convert_to_canonical_form(self):
        """Convert the model into canonical form."""
        artificial_vars = len(self._constraints)

        self._canonical_constraints = []
        artificial_var_idx = 0
        coeff_acc = [0] * len(self.variables)
        free_term_acc = 0
        for coefficients, free_term in self._standard_constraints:
            if free_term < 0:
                coefficients = _vec_scalar(coefficients, -1)
                free_term *= -1
            artificial_coeff = [0] * artificial_vars
            artificial_coeff[artificial_var_idx] = 1
            artificial_var_idx += 1
            self._canonical_constraints.append(
                (coefficients + artificial_coeff, free_term))

            coeff_acc = _vec_plus_vec(coeff_acc, coefficients)
            free_term_acc += free_term

        coefficients, free_term = self._standard_cost_function
        artificial_coeff = [0] * artificial_vars
        self._canonical_cost_function = (coefficients + artificial_coeff,
                                         free_term)

        coeff_acc = _vec_scalar(coeff_acc, -1)
        self._canonical_artificial_function = (coeff_acc + artificial_coeff,
                                               -free_term_acc)

    def _build_tableau_canonical_form(self):
        """Build the tableau related with the canonical form."""
        # Total number of variables
        n = len(self._canonical_artificial_function[0])
        # Basic variables (in canonical form there is one per constraint)
        m = len(self._constraints)
        tableau = Tableau(n, m)
        canonical_constraints = enumerate(self._canonical_constraints)
        for (idx, (coefficients, free_term)) in canonical_constraints:
            tableau.add_constraint(coefficients + [free_term], n - m + idx)

        coefficients, free_term = self._canonical_cost_function
        tableau.add_cost_function(coefficients + [free_term])

        coefficients, free_term = self._canonical_artificial_function
        tableau.add_artificial_function(coefficients + [free_term])
        return tableau


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

        self._artificial = False

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

    def add_artificial_function(self, artificial_function):
        """Add the artificial function in the tableau."""
        assert len(artificial_function) == self.n + 1, \
            'Wrong size for the cost function'
        assert len(self._basic_variables) == len(self._tableau) - 1 \
            and len(self._tableau) == self.m + 1, 'Too few constraints or ' \
            'not cost function registered'

        self._artificial = True
        self._tableau.append(artificial_function)

    def constraints(self):
        """Return the constraints in the tableau."""
        last = -1 if not self._artificial else -2
        return self._tableau[:last]

    def cost_function(self):
        """Return the cost function in the tableau."""
        # If we use the artificial cost function, is still in the last
        # position.
        return self._tableau[-1]

    def drop_artificial(self):
        """Transform the tableau in one without artificial variables."""
        assert self._artificial, 'Tableau already without artificial variables'
        assert self.is_minimum(), 'Tableau is not in minimum state'

        # Check that the basic variables are not artificial variables
        artificial_variables = range(self.n - self.m, self.n)
        assert not any(i in self._basic_variables
                       for i in artificial_variables), \
            'At least one artificial variable is a basic variable'

        # Remove the artificial cost function
        self._tableau.pop()

        # Drop all artificial variable coefficients
        tableau = []
        for line in self._tableau:
            tableau.append(line[:-self.m - 1] + [line[-1]])
        self._tableau = tableau

        self._artificial = False

    def simplex(self):
        """Resolve the constraints via the simplex algorithm."""
        while not self.is_minimum():
            column = self._get_pivoting_column()
            row = self._get_pivoting_row(column)
            self._pivote(row, column)
            self._basic_variables[row] = column

    def is_canonical(self):
        """Check if is in canonical form."""
        result = True

        # The system of constraints is in canonical form
        for idx, constraint in zip(self._basic_variables,
                                   self.constraints()):
            result = result and all(
                constraint[i] == (1 if idx == i else 0)
                for i in self._basic_variables)

        # We need to check that the associated basic solution is
        # feasible. But we separate this check in a different method.
        # result = result and self.is_basic_feasible_solution()

        # The objective function is expressed in therms of only the
        # nonbasic variables
        cost_function = self.cost_function()
        result = result and all(cost_function[i] == 0
                                for i in self._basic_variables)
        return result

    def is_minimum(self):
        """Check if the cost function is already minimized."""
        return all(c >= 0 for c in self.cost_function()[:-1])

    def is_basic_feasible_solution(self):
        """Check if there is a basic feasible solution."""
        assert self.is_canonical(), 'Tableau is not in canonical form'

        if self._artificial:
            assert self.is_minimum(), 'If there are artificial variables, ' \
                'we need to be minimized.'
            return self.cost_functions()[-1] == 0
        else:
            return all(c[-1] >= 0 for c in self.constraints())

    def is_bound(self):
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
        # NOTE(aplanas): Not sure that this is the case
        assert candidates, 'Not basic feasible solution found.'
        return min(candidates, key=lambda x: x[1])[0]

    def _pivote(self, row, column):
        """Pivote the tableau in (row, column)."""
        # Normalize the row
        vec = _vec_scalar(
            self._tableau[row], 1 / self._tableau[row][column])
        self._tableau[row] = vec
        for row_b, vec_b in enumerate(self._tableau):
            if row_b != row:
                self._tableau[row_b] = _vec_vec_scalar(
                    vec, vec_b, -vec_b[column])
