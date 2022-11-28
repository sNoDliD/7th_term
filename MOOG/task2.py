import json
from functools import lru_cache

import matplotlib as mpl
import numpy as np
from matplotlib import pyplot as plt, cm

mpl.use('Qt5Agg')


def show_data(data, points=None):
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    if points:
        points = np.array(points)
        ax.scatter(points[:, 0], points[:, 1], points[:, 2], depthshade=False)
    ax.plot_surface(data[:, :, 0], data[:, :, 1], data[:, :, 2], cmap=cm.coolwarm, linewidth=5)

    # fig.show()
    plt.show()


def get_params_vector(points_vector):
    n = len(points_vector)
    result = np.zeros(n, dtype="float32")
    result[n - 1] = 1

    distances = [np.linalg.norm(points_vector[i] - points_vector[i - 1]) for i in range(1, n)]
    total = sum(distances)
    for i in range(1, n - 1):
        result[i] = result[i - 1] + distances[i - 1] / total
    return result


def get_s_vector(parameters_matrix):
    n = len(parameters_matrix)

    result = np.zeros(n, dtype="float32")
    for i in range(n):
        result[i] = sum(parameters_matrix[:, i]) / n
    return result


class Surface:
    knots_column: np.array
    knots_row: np.array
    control_points: np.array

    def __init__(self, size, data, *args, basis_degree, initial_points, **kwargs):
        self.size = size
        self.data = data
        self.k = basis_degree
        self.initial_points = initial_points

        self.initialize()

    @classmethod
    def init_from_file(cls, filename, **kwargs):
        with open(filename) as file:
            file_data = json.load(file)
        surface = file_data["surface"]

        size = surface['gridSize']
        data = np.zeros([*size, 3], dtype='float32')
        for point, (x, y) in zip(surface['points'], surface['indices']):
            data[x, y] = point
        return cls(size, data, initial_points=surface['points'], **kwargs)

    def initialize(self):
        n = self.size[0]

        column_matrix = np.zeros((n, n), dtype="float32")
        row_matrix = np.zeros((n, n), dtype="float32")
        for i in range(n):
            column_matrix[i] = get_params_vector(self.data[:, i])
            row_matrix[i] = get_params_vector(self.data[i])
        s_column = get_s_vector(column_matrix)
        s_row = get_s_vector(row_matrix)

        self.generate_knots(s_column, s_row)
        self.generate_control_points(s_column, s_row)

    @lru_cache(2 ** 12)
    def basis_function(self, t, i, k, is_row):
        knot_vector = self.knots_row if is_row else self.knots_column
        if k == 0:
            return 1 if knot_vector[i] <= t <= knot_vector[i + 1] else 0

        term_1 = 0
        delta = (knot_vector[i + k] - knot_vector[i])
        if not np.isclose(delta, 0):
            term_1 = self.basis_function(t, i, k - 1, is_row) * (t - knot_vector[i]) / delta

        term_2 = 0
        delta = (knot_vector[i + k + 1] - knot_vector[i + 1])
        if not np.isclose(delta, 0):
            term_2 = self.basis_function(t, i + 1, k - 1, is_row) * (knot_vector[i + k + 1] - t) / delta

        return term_1 + term_2

    def generate_knots(self, s_column, s_row):
        k = self.k
        n = self.size[0]
        knots_num = n + k + 1

        self.knots_column = np.zeros(knots_num, dtype="float32")
        self.knots_row = np.zeros(knots_num, dtype="float32")

        for j in range(1, n - k):
            self.knots_column[j + k] = 1 / k * sum(s_column[j: j + k])
            self.knots_row[j + k] = 1 / k * sum(s_row[j: j + k])

        for j in range(k + 1):
            self.knots_column[j] = 0
            self.knots_row[j] = 0
            self.knots_column[knots_num - j - 1] = 1
            self.knots_row[knots_num - j - 1] = 1

    def generate_control_points(self, s_column, s_row):
        n = self.size[0]
        k = self.k

        q_matrix = np.zeros((n, n, 3))
        self.control_points = np.zeros((n, n, 3))
        temp_matrix = np.zeros((n, n), dtype="float32")

        for d in range(n):
            for i in range(n):
                for j in range(n):
                    temp_matrix[i, j] = self.basis_function(s_column[i], j, k, False)
            q_matrix[:, d] = np.linalg.solve(temp_matrix, self.data[:, d])

        for c in range(n):
            for i in range(n):
                for j in range(n):
                    temp_matrix[i, j] = self.basis_function(s_row[i], j, k, True)
            self.control_points[c] = np.linalg.solve(temp_matrix, q_matrix[c])

    def get_point_on_surface(self, u, v):
        n = self.size[0]
        k = self.k
        result = np.zeros(3)

        for i in range(n):
            temp = 0
            for j in range(n):
                n_j_k = self.basis_function(v, j, k, True)
                current_term = n_j_k * self.control_points[i, j]
                temp += current_term
            n_i_k = self.basis_function(u, i, k, False)
            result += temp * n_i_k

        return result

    def approximation(self, points_count: int):
        data = np.zeros([points_count, points_count, 3], dtype='float32')
        t = np.linspace(0, 1, points_count)
        for u in range(points_count):
            for v in range(points_count):
                data[u, v] = self.get_point_on_surface(t[u], t[v])
        return data


def main():
    surface = Surface.init_from_file("9.json", basis_degree=3)
    data = surface.approximation(30)
    show_data(data, points=surface.initial_points)


if __name__ == '__main__':
    main()
