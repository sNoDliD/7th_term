import json

import matplotlib as mpl
import numpy as np
from matplotlib import collections as mc
from matplotlib import pyplot as plt

mpl.use('Qt5Agg')


def load_points(filepath):
    with open(filepath) as file:
        task_data = json.load(file)
    points = task_data["curve"]
    points.append(points[0])
    points = np.array(points)
    return points


def get_control_points(key_points):
    points_n = len(key_points)
    matrix_n = 2 * points_n - 2

    matrix = np.zeros((matrix_n, matrix_n))
    vector = np.zeros((matrix_n, 2))

    for i in range(points_n):
        if i == 0:
            matrix[i][i:i + 2] = [2, -1]
            vector[i] = key_points[i]
        elif i == (points_n - 1):
            matrix[2 * i - 1][2 * i - 2:2 * i] = [-1, 2]
            vector[2 * i - 1] = key_points[i]
        else:
            matrix[2 * i - 1][2 * i - 1:2 * i + 1] = [1, 1]
            matrix[2 * i][2 * i - 2:2 * i + 2] = [1, -2, 2, -1]
            vector[2 * i - 1] = 2 * key_points[i]
    return np.linalg.solve(matrix, vector)


def lerp(a, b, t):
    return a * (1 - t) + b * t


def bezier(p0, p1, p2, p3, t):
    return lerp(lerp(lerp(p0, p1, t), lerp(p1, p2, t), t), lerp(lerp(p1, p2, t), lerp(p2, p3, t), t), t)


def show_data(points, control_points):
    bezier_points = []
    for i, (p_start, p_end) in enumerate(zip(points, points[1:])):
        control_1, control_2 = control_points[2 * i: 2 * i + 2]
        for t in np.linspace(0, 1, 30, False):
            bezier_points.append(bezier(p_start, control_1, control_2, p_end, t))
    bezier_points = np.array(bezier_points)

    fig, ax = plt.subplots()
    ax.plot(bezier_points[:, 0], bezier_points[:, 1], color='darkorchid', linewidth=2)
    ax.scatter(points[:, 0], points[:, 1], c='darkorchid')

    # control lines
    lines = []
    for i, point in enumerate(points):
        if i == 0:
            lines.append([control_points[0], point])
            continue
        if i == len(points) - 1:
            lines.append([point, control_points[-1]])
            continue
        left, right = control_points[2 * i - 1: 2 * i + 1]
        lines.append([left, point])
        lines.append([point, right])
    lc = mc.LineCollection(np.array(lines), colors='green', linewidths=3)
    ax.add_collection(lc)
    ax.scatter(control_points[:, 0], control_points[:, 1], c='green')

    plt.show()


def main():
    points = load_points("9.json")
    control_points = get_control_points(points)
    show_data(points, control_points)


if __name__ == '__main__':
    main()
