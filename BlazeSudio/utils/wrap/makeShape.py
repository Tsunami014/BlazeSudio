import math
import numpy as np

from ._core import (
    theta,
    d_theta,
    _polygon_fill,
    _skeletonize,
    _skeleton_to_paths,
    _polygon_buffer,
)

__all__ = [
    'FindRadius',
    'WrapJoints',
    'FindBounds',
    'OverConstrainedError',
]


class OverConstrainedError(ValueError):
    """
    The expression has been overly constrained and will not output a closed circle!
    """


def FindRadius(jointDists, epsilon=0.0000002, max_iters=1000, returnIterations=False) -> (float | tuple[float, int]):
    min_theta = 1.0 - epsilon
    max_theta = 1.0 + epsilon

    desired_angle = 360
    DA_ratio = desired_angle / 360

    sum_length = sum(jointDists)
    max_length = max(jointDists)

    if max_length >= sum_length/2:
        raise ValueError(
            "Not a valid polygon; one of the line segments is too long."
        )

    min_radius = 0.5 * max_length
    max_radius = (0.5 * sum_length) / DA_ratio

    iterations = 0

    while True:
        sum_theta = 0.0
        iterations += 1
        radius = 0.5 * (min_radius + max_radius)

        for L in jointDists:
            sum_theta += theta(L, radius)

        sum_theta /= (2 * math.pi) * DA_ratio

        if min_theta <= sum_theta <= max_theta:
            break
        elif sum_theta < 1.0:
            max_radius = radius
        else:
            min_radius = radius

        if max_iters is not None and iterations > max_iters:
            if sum_theta < 1.0:
                too = 'small'
            else:
                too = 'large'
            raise TimeoutError(
                'Maximum iterations reached! Radius was too %s. Couldn\'t put the points on a circle, try a different arrangement of points'%too
            )

    if returnIterations:
        return radius, iterations

    return radius


# Thanks SO MUCH to https://math.stackexchange.com/questions/1930607/maximum-area-enclosure-given-side-lengths
def WrapJoints(joints: list[tuple[int, int]], setAngs: list[int], *, return_radius: bool = False
        ) -> (list[tuple[int, int]] | tuple[list[tuple[int, int]], float]):
    # TODO: Multiple constraints in a row
    # TODO: Paralell constraints

    prevj = None
    jointDists = []
    for j in joints:
        if prevj is None:
            prevj = j
            continue
        if prevj[1] == j[1]:
            jointDists.append(j[0]-prevj[0])
        elif prevj[0] == j[0]:
            jointDists.append(j[1]-prevj[1])
        else:
            jointDists.append(math.sqrt((j[0]-prevj[0])**2+(j[1]-prevj[1])**2))
        prevj = j

    if len(jointDists) < 3:
        raise ValueError(
            "Need at least three line lengths."
        )

    radius = FindRadius(jointDists)

    startingi = 0
    got = 0
    for i in range(len(setAngs)):
        if setAngs[i] is not None:
            if got == 0:
                startingi = i
                got = 1
            elif got == 2:
                raise OverConstrainedError(
                    'Cannot have multiple constraints not in a row!'
                )
        elif got == 1:
            got = 2

    phi = -0.5 * theta(jointDists[startingi], radius)
    if got != 0:
        phi += math.radians(setAngs[startingi])

    x0 = radius * math.cos(phi)
    y0 = -radius * math.sin(phi)

    njs = []

    for i in range(len(jointDists)):
        L = jointDists[(i+startingi) % len(jointDists)]
        x = x0 - radius * math.cos(phi)
        y = y0 + radius * math.sin(phi)
        phi += theta(L, radius)
        njs.append((x, y))
    out = [njs[i-startingi] for i in range(len(njs))] + [njs[-startingi]]
    if return_radius:
        return out, radius
    return out


def FindBounds(radius: float, joints: list[tuple[int, int]], hei,
        *, large=True, small=True, arc_segments=16):
    if large:
        lgeObj = _polygon_buffer(list(joints), hei, arc_segments)
    else:
        lgeObj = None

    if small:
        xs, ys = zip(*joints)
        minx, miny = min(xs), min(ys)
        image = np.zeros((int(math.ceil(max(xs)-minx))+1, int(math.ceil(max(ys)-miny))+1), dtype=np.uint8)
        rr, cc = _polygon_fill(np.array(xs)-minx, np.array(ys)-miny)
        rr = np.clip(rr, 0, image.shape[0]-1)
        cc = np.clip(cc, 0, image.shape[1]-1)
        image[rr, cc] = 1
        skeleton = _skeletonize(image)
        paths = _skeleton_to_paths(skeleton)
        smlObj = [
            ((float(u[0])+minx, float(u[1])+miny), (float(v[0])+minx, float(v[1])+miny)) for path in paths for u, v in zip(path[:-1], path[1:])
        ]
    else:
        smlObj = None

    return lgeObj, smlObj
