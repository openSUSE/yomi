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

import unittest

from utils import lp


class ModelTestCase(unittest.TestCase):

    def test_add_constraint_fails(self):
        """Test Model.add_constraint asserts."""
        model = lp.Model(['x1', 'x2'])
        self.assertRaises(AssertionError, model.add_constraint, [1],
                          lp.EQ, 1)
        self.assertRaises(AssertionError, model.add_constraint,
                          [1, 2, 3], lp.EQ, 1)
        self.assertRaises(AssertionError, model.add_constraint,
                          [1, 2], None, 1)

    def test_add_constraint(self):
        """Test Model.add_constraint success."""
        model = lp.Model(['x1', 'x2'])
        model.add_constraint([1, 2], lp.EQ, 1)
        self.assertTrue(([1, 2], lp.EQ, 1) in model._constraints)

    def test_add_cost_function_fails(self):
        """Test Model.add_cost_function asserts."""
        model = lp.Model(['x1', 'x2'])
        self.assertRaises(AssertionError, model.add_cost_function,
                          None, [1, 2], 1)
        self.assertRaises(AssertionError, model.add_cost_function,
                          lp.MINIMIZE, [1], 1)
        self.assertRaises(AssertionError, model.add_cost_function,
                          lp.MINIMIZE, [1, 2, 3], 1)

    def test_add_cost_function(self):
        """Test Model.add_cost_function success."""
        model = lp.Model(['x1', 'x2'])
        model.add_cost_function(lp.MINIMIZE, [1, 2], 1)
        self.assertEqual((lp.MINIMIZE, [1, 2], 1), model._cost_function)

    def test_simplex(self):
        """Test Model.simplex."""
        model = lp.Model(['x1', 'x2', 'x3', 'x4', 'x5'])
        model.add_constraint([-6, 0, 1, -2, 2], lp.EQ, 6)
        model.add_constraint([-3, 1, 0, 6, 3], lp.EQ, 15)
        model.add_cost_function(lp.MINIMIZE, [5, 0, 0, 3, -2], -21)
        self.assertEqual(model.simplex(), {
            'x1': 1.0, 'x2': 0.0, 'x3': 0.0, 'x4': 0.0, 'x5': 6.0})

    def test__convert_to_standard_form_standard(self):
        """Test Model._convert_to_standard_form when in standard form."""
        model = lp.Model(['x1', 'x2', 'x3'])
        model.add_constraint([30, 100, 85], lp.EQ, 2500)
        model.add_constraint([6, 2, 3], lp.EQ, 90)
        model.add_cost_function(lp.MINIMIZE, [3, 2, 4], 0)
        model._convert_to_standard_form()
        self.assertEqual(model._slack_variables, [])
        self.assertEqual(model._standard_constraints,
                         [([30, 100, 85], 2500),
                          ([6, 2, 3], 90)])
        self.assertEqual(model._standard_cost_function, ([3, 2, 4], 0))

    def test__convert_to_standard_form_lte(self):
        """Test Model._convert_to_standard_form when constraint is LTE."""
        model = lp.Model(['x1', 'x2', 'x3'])
        model.add_constraint([30, 100, 85], lp.LTE, 2500)
        model.add_constraint([6, 2, 3], lp.EQ, 90)
        model.add_cost_function(lp.MINIMIZE, [3, 2, 4], 0)
        model._convert_to_standard_form()
        self.assertEqual(model._slack_variables, [3])
        self.assertEqual(model._standard_constraints,
                         [([30, 100, 85, 1], 2500),
                          ([6, 2, 3, 0], 90)])
        self.assertEqual(model._standard_cost_function, ([3, 2, 4, 0], 0))

    def test__convert_to_standard_form_gte(self):
        """Test Model._convert_to_standard_form when constraint is GTE."""
        model = lp.Model(['x1', 'x2', 'x3'])
        model.add_constraint([30, 100, 85], lp.GTE, 2500)
        model.add_constraint([6, 2, 3], lp.EQ, 90)
        model.add_cost_function(lp.MINIMIZE, [3, 2, 4], 0)
        model._convert_to_standard_form()
        self.assertEqual(model._slack_variables, [3])
        self.assertEqual(model._standard_constraints,
                         [([30, 100, 85, -1], 2500),
                          ([6, 2, 3, 0], 90)])
        self.assertEqual(model._standard_cost_function, ([3, 2, 4, 0], 0))

    def test__convert_to_standard_form_lte_gte(self):
        """Test Model._convert_to_standard_form for LTE/GTE constraints."""
        model = lp.Model(['x1', 'x2', 'x3'])
        model.add_constraint([30, 100, 85], lp.LTE, 2500)
        model.add_constraint([6, 2, 3], lp.GTE, 90)
        model.add_cost_function(lp.MINIMIZE, [3, 2, 4], 0)
        model._convert_to_standard_form()
        self.assertEqual(model._slack_variables, [3, 4])
        self.assertEqual(model._standard_constraints,
                         [([30, 100, 85, 1, 0], 2500),
                          ([6, 2, 3, 0, -1], 90)])
        self.assertEqual(model._standard_cost_function,
                         ([3, 2, 4, 0, 0], 0))

    def test__convert_to_standard_form_maximize(self):
        """Test Model.c_onvert_to_standard_form when maximizing."""
        model = lp.Model(['x1', 'x2', 'x3'])
        model.add_constraint([30, 100, 85], lp.EQ, 2500)
        model.add_constraint([6, 2, 3], lp.EQ, 90)
        model.add_cost_function(lp.MAXIMIZE, [3, 2, 4], 0)
        model._convert_to_standard_form()
        self.assertEqual(model._slack_variables, [])
        self.assertEqual(model._standard_constraints,
                         [([30, 100, 85], 2500),
                          ([6, 2, 3], 90)])
        self.assertEqual(model._standard_cost_function, ([-3, -2, -4], 0))

    def test__convert_to_canonical_form(self):
        """Test Model._convert_to_canonical_form when in standard form."""
        model = lp.Model(['x1', 'x2', 'x3', 'x4'])
        model.add_constraint([1, -2, -3, -2], lp.EQ, 3)
        model.add_constraint([1, -1, 2, 1], lp.EQ, 11)
        model.add_cost_function(lp.MINIMIZE, [2, -3, 1, 1], 0)
        model._convert_to_standard_form()
        model._convert_to_canonical_form()
        self.assertEqual(model._canonical_constraints,
                         [([1, -2, -3, -2, 1, 0], 3),
                          ([1, -1, 2, 1, 0, 1], 11)])
        self.assertEqual(model._canonical_cost_function,
                         ([2, -3, 1, 1, 0, 0], 0))
        self.assertEqual(model._canonical_artificial_function,
                         ([-2, 3, 1, 1, 0, 0], -14))

    def test__convert_to_canonical_form_neg_free_term(self):
        """Test Model._convert_to_standard_form when in standard form."""
        model = lp.Model(['x1', 'x2', 'x3'])
        model.add_constraint([30, 100, 85], lp.EQ, -2500)
        model.add_constraint([6, 2, 3], lp.EQ, 90)
        model.add_cost_function(lp.MINIMIZE, [3, 2, 4], 0)
        model._convert_to_standard_form()
        model._convert_to_canonical_form()
        self.assertEqual(model._canonical_constraints,
                         [([-30, -100, -85, 1, 0], 2500),
                          ([6, 2, 3, 0, 1], 90)])
        self.assertEqual(model._canonical_cost_function, ([3, 2, 4, 0, 0], 0))
        self.assertEqual(model._canonical_artificial_function,
                         ([24, 98, 82, 0, 0], -2590))

    def test__build_tableau_canonical_form(self):
        """Test Model._build_tableau_canonical_form method."""
        model = lp.Model(['x1', 'x2', 'x3', 'x4'])
        model.add_constraint([1, -2, -3, -2], lp.EQ, 3)
        model.add_constraint([1, -1, 2, 1], lp.EQ, 11)
        model.add_cost_function(lp.MINIMIZE, [2, -3, 1, 1], 0)
        model._convert_to_standard_form()
        model._convert_to_canonical_form()
        tableau = model._build_tableau_canonical_form()
        self.assertEqual(tableau._basic_variables, [4, 5])
        self.assertEqual(tableau._tableau,
                         [[1, -2, -3, -2, 1, 0, 3],
                          [1, -1, 2, 1, 0, 1, 11],
                          [2, -3, 1, 1, 0, 0, 0],
                          [-2, 3, 1, 1, 0, 0, -14]])


class TableauTestCase(unittest.TestCase):

    def test_add_constraint_fails(self):
        """Test Tableau.add_constraint asserts."""
        tableau = lp.Tableau(3, 2)
        self.assertRaises(AssertionError, tableau.add_constraint, [1], 0)
        self.assertRaises(AssertionError, tableau.add_constraint,
                          [1, 2, 3, 4, 5], 0)
        tableau.add_constraint([1, 2, 3, 4], 0)
        self.assertRaises(AssertionError, tableau.add_constraint,
                          [1, 2, 3, 4], 0)

    def test_add_constraint(self):
        """Test Tableau.add_constraint success."""
        tableau = lp.Tableau(3, 2)
        tableau.add_constraint([1, 2, 3, 4], 0)
        self.assertEqual(tableau._basic_variables, [0])
        self.assertEqual(tableau._tableau, [[1, 2, 3, 4]])

    def test_add_cost_function_fails(self):
        """Test Tableau.add_cost_function asserts."""
        tableau = lp.Tableau(3, 2)
        self.assertRaises(AssertionError, tableau.add_cost_function, [1])
        self.assertRaises(AssertionError, tableau.add_cost_function,
                          [1, 2, 3, 4])

    def test_add_cost_function(self):
        """Test Tableau.add_cost_function success."""
        tableau = lp.Tableau(3, 2)
        tableau.add_constraint([1, 2, 3, 4], 0)
        tableau.add_constraint([0, 1, 2, 3], 1)
        tableau.add_cost_function([0, 0, 1, 2])
        self.assertEqual(tableau._tableau, [[1, 2, 3, 4],
                                            [0, 1, 2, 3],
                                            [0, 0, 1, 2]])

    def test_add_artificial_function_fails(self):
        """Test Tableau.add_artificial_function asserts."""
        tableau = lp.Tableau(3, 2)
        self.assertRaises(AssertionError, tableau.add_artificial_function, [1])
        self.assertRaises(AssertionError, tableau.add_artificial_function,
                          [1, 2, 3, 4])

    def test_add_artificial_function(self):
        """Test Tableau.add_artificial_function success."""
        tableau = lp.Tableau(3, 2)
        tableau.add_constraint([1, 2, 3, 4], 0)
        tableau.add_constraint([0, 1, 2, 3], 1)
        tableau.add_cost_function([0, 0, 1, 2])
        tableau.add_artificial_function([1, 3, 5, 7])
        self.assertTrue(tableau._artificial)
        self.assertEqual(tableau._tableau, [[1, 2, 3, 4],
                                            [0, 1, 2, 3],
                                            [0, 0, 1, 2],
                                            [1, 3, 5, 7]])

    def test_constraints(self):
        """Test Tableau.constraints method."""
        tableau = lp.Tableau(3, 2)
        tableau.add_constraint([1, 2, 3, 4], 0)
        tableau.add_constraint([0, 1, 2, 3], 1)
        tableau.add_cost_function([0, 0, 1, 2])
        tableau.add_artificial_function([1, 3, 5, 7])
        self.assertEqual(tableau.constraints(), [[1, 2, 3, 4],
                                                 [0, 1, 2, 3]])

    def test_cost_function(self):
        """Test Tableau.cost_function for non artificial models."""
        tableau = lp.Tableau(3, 2)
        tableau.add_constraint([1, 2, 3, 4], 0)
        tableau.add_constraint([0, 1, 2, 3], 1)
        tableau.add_cost_function([0, 0, 1, 2])
        self.assertEqual(tableau.cost_function(), [0, 0, 1, 2])

    def test_cost_function_artificial(self):
        """Test Tableau.cost_function for artificial models."""
        tableau = lp.Tableau(3, 2)
        tableau.add_constraint([1, 2, 3, 4], 0)
        tableau.add_constraint([0, 1, 2, 3], 1)
        tableau.add_cost_function([0, 0, 1, 2])
        tableau.add_artificial_function([1, 3, 5, 7])
        self.assertEqual(tableau.cost_function(), [1, 3, 5, 7])

    def test_drop_artificial_not_minimal(self):
        """Test Tableau.drop_artificial fails when not minimal."""
        tableau = lp.Tableau(4, 2)
        tableau.add_constraint([1, 2, 1, 0, 5], 0)
        tableau.add_constraint([0, 1, 0, 1, 5], 1)
        tableau.add_cost_function([2, 3, 0, 0, 5])
        tableau.add_artificial_function([-1, -3, 0, 0, -15])
        self.assertRaises(AssertionError, tableau.drop_artificial)

    def test_drop_artificial_artificial_variable(self):
        """Test Tableau.drop_artificial fails when artificial variable."""
        tableau = lp.Tableau(4, 2)
        tableau.add_constraint([1, 2, 1, 0, 5], 2)
        tableau.add_constraint([0, 1, 0, 1, 5], 3)
        tableau.add_cost_function([2, 3, 0, 0, 5])
        tableau.add_artificial_function([1, 3, 0, 0, -15])
        self.assertRaises(AssertionError, tableau.drop_artificial)

    def test_drop_artificial(self):
        """Test Tableau.drop_artificial method."""
        tableau = lp.Tableau(4, 2)
        tableau.add_constraint([1, 2, 1, 0, 5], 0)
        tableau.add_constraint([0, 1, 0, 1, 5], 1)
        tableau.add_cost_function([2, 3, 0, 0, 5])
        tableau.add_artificial_function([1, 3, 0, 0, -15])
        tableau.drop_artificial()
        self.assertFalse(tableau._artificial)
        self.assertEqual(tableau._tableau, [[1, 2, 5],
                                            [0, 1, 5],
                                            [2, 3, 5]])

    def test_simplex(self):
        """Test Tableau.simplex method."""
        tableau = lp.Tableau(5, 2)
        tableau.add_constraint([-6, 0, 1, -2, 2, 6], 2)
        tableau.add_constraint([-3, 1, 0, 6, 3, 15], 1)
        tableau.add_cost_function([5, 0, 0, 3, -2, -21])
        tableau.simplex()
        self.assertEqual(tableau._basic_variables, [4, 0])
        self.assertEqual(tableau._tableau,
                         [[0.0, 1/2, -1/4, 7/2, 1.0, 6.0],
                          [1.0, 1/6, -1/4, 3/2, 0.0, 1.0],
                          [0.0, 1/6, 3/4, 5/2, 0.0, -14.0]])

    def test_is_canonical_not_canonical(self):
        """Test Tableau.is_canonical when not canonical."""
        tableau = lp.Tableau(3, 2)
        tableau.add_constraint([1, 2, 0, 5], 1)
        tableau.add_constraint([0, 1, 0, 5], 2)
        tableau.add_cost_function([2, 3, 0, 5])
        self.assertFalse(tableau.is_canonical())

    def test_is_canonical_almost_canonical(self):
        """Test Tableau.is_canonical when no canonical."""
        tableau = lp.Tableau(2, 2)
        tableau.add_constraint([1, 2, 5], 0)
        tableau.add_constraint([0, 1, 5], 1)
        tableau.add_cost_function([2, 3, 5])
        self.assertFalse(tableau.is_canonical())

    def test_is_canonical(self):
        """Test Tableau.is_canonical when canonical."""
        tableau = lp.Tableau(2, 2)
        tableau.add_constraint([1, 0, 5], 0)
        tableau.add_constraint([0, 1, 5], 1)
        tableau.add_cost_function([0, 0, 5])
        self.assertTrue(tableau.is_canonical())

    def test_is_minimum_not_minimum(self):
        """Test Tableau.is_minimum method."""
        tableau = lp.Tableau(3, 2)
        tableau.add_constraint([1, 2, 3, 4], 0)
        tableau.add_constraint([0, 1, 2, 3], 1)
        tableau.add_cost_function([0, 0, -1, 2])
        self.assertFalse(tableau.is_minimum())

    def test_is_minimum_artificial_not_minimum(self):
        """Test Tableau.is_minimum method."""
        tableau = lp.Tableau(3, 2)
        tableau.add_constraint([1, 2, 3, 4], 0)
        tableau.add_constraint([0, 1, 2, 3], 1)
        tableau.add_cost_function([0, 0, 1, 2])
        tableau.add_artificial_function([2, -3, 0, 0])
        self.assertFalse(tableau.is_minimum())

    def test_is_minimum(self):
        """Test Tableau.is_minimum method."""
        tableau = lp.Tableau(3, 2)
        tableau.add_constraint([1, 2, 3, 4], 0)
        tableau.add_constraint([0, 1, 2, 3], 1)
        tableau.add_cost_function([0, 0, 1, 2])
        self.assertTrue(tableau.is_minimum())

    def test_is_minimum_artificial(self):
        """Test Tableau.is_minimum method."""
        tableau = lp.Tableau(3, 2)
        tableau.add_constraint([1, 2, 3, 4], 0)
        tableau.add_constraint([0, 1, 2, 3], 1)
        tableau.add_cost_function([0, 0, -1, 2])
        tableau.add_artificial_function([2, 3, 0, 0])
        self.assertTrue(tableau.is_minimum())

    def test_is_basic_feasible_solution_fails(self):
        """Test Tableau.is_basic_feasible_solution failures."""
        tableau = lp.Tableau(4, 2)
        tableau.add_constraint([1, 1, 2, 1, 6], 0)
        tableau.add_constraint([0, 3, 1, 8, 3], 1)
        tableau.add_cost_function([0, 0, 0, 0, 0])
        self.assertRaises(AssertionError, tableau.is_basic_feasible_solution)

    def test_is_basic_feasible_solution_non_existent(self):
        """Test Tableau.is_basic_feasible_solution method."""
        tableau = lp.Tableau(4, 2)
        tableau.add_constraint([1, 0, 1.667, 1.667, 5], 0)
        tableau.add_constraint([0, 1, 0.333, 2.667, -1], 1)
        tableau.add_cost_function([0, 0, 0, 0, 0])
        self.assertFalse(tableau.is_basic_feasible_solution())

    def test_is_basic_feasible_solution(self):
        """Test Tableau.is_basic_feasible_solution method."""
        tableau = lp.Tableau(4, 2)
        tableau.add_constraint([1, 0, 1.667, 1.667, 5], 0)
        tableau.add_constraint([0, 1, 0.333, 2.667, 1], 1)
        tableau.add_cost_function([0, 0, 0, 0, 0])
        self.assertTrue(tableau.is_basic_feasible_solution())

    def test_is_bound(self):
        """Test Tableau.is_bound method."""
        pass

    def test__get_pivoting_column(self):
        """Test Tableau._get_pivoting_column method."""
        tableau = lp.Tableau(5, 2)
        tableau.add_constraint([-6, 0, 1, -2, 2, 6], 2)
        tableau.add_constraint([-3, 1, 0, 6, 3, 15], 1)
        tableau.add_cost_function([5, 0, 0, 3, -2, -21])
        self.assertEqual(tableau._get_pivoting_column(), 4)

    def test__get_pivoting_row(self):
        """Test Tableau._get_pivoting_row method."""
        tableau = lp.Tableau(5, 2)
        tableau.add_constraint([-6, 0, 1, -2, 2, 6], 2)
        tableau.add_constraint([-3, 1, 0, 6, 3, 15], 1)
        tableau.add_cost_function([5, 0, 0, 3, -2, -21])
        self.assertEqual(tableau._get_pivoting_row(4), 0)

    def test__pivote(self):
        """Test Tableau._pivote method."""
        tableau = lp.Tableau(3, 3)
        tableau.add_constraint([1, 4, 2, 6], 0)
        tableau.add_constraint([3, 14, 8, 16], 1)
        tableau.add_constraint([4, 21, 10, 28], 2)

        # Pivote by x1 in the first equation
        tableau._pivote(0, 0)
        self.assertEqual(tableau._tableau,
                         [[1.0, 4.0, 2.0, 6.0],
                          [0.0, 2.0, 2.0, -2.0],
                          [0.0, 5.0, 2.0, 4.0]])
        # Pivote by x2 in the second equation
        tableau._pivote(1, 1)
        self.assertEqual(tableau._tableau,
                         [[1.0, 0.0, -2.0, 10.0],
                          [0.0, 1.0, 1.0, -1.0],
                          [0.0, 0.0, -3.0, 9.0]])
        # Pivote by x3 in the third equation
        tableau._pivote(2, 2)
        self.assertEqual(tableau._tableau,
                         [[1.0, 0.0, 0.0, 4.0],
                          [0.0, 1.0, 0.0, 2.0],
                          [0.0, 0.0, 1.0, -3.0]])


if __name__ == '__main__':
    unittest.main()
