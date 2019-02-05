
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
        self._tableau[row] = [a * value for a in self._tableau[row]]

    def _linear(self, row_a, row_b, value):
        """Linear combination of two rows and a value."""
        self._tableau[row_b] = [a * value + b
                                for a, b in zip(self._tableau[row_a],
                                                self._tableau[row_b])]

    def _pivote(self, row, column):
        """Pivote the tableau in (row, column)."""
        # Normalize the row
        self._scalar(row, 1 / self._tableau[row][column])
        for row_b in range(len(self._tableau)):
            if row != row_b:
                self._linear(row, row_b, -self._tableau[row_b][column])


if __name__ == 'main':
    pass
