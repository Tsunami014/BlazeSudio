import math
import numpy as np
import BlazeSudio.collisions as colls

__all__ = [
    'FindRadius',
    'WrapJoints',
    'FindBounds',
    'OverConstrainedError',
]

def theta(L, r):
    return 2.0 * math.asin(0.5 * L / r)

def d_theta(L, r):
    r2 = r * r
    return -2.0 * L / (r2 * math.sqrt(4.0 - L * L / r2))


def _polygon_fill(r_coords, c_coords):
    """
    Rasterize a polygon given row (r) and column (c) vertex coordinates,
    returning (rr, cc) arrays of filled pixel coordinates.

    Equivalent in spirit to skimage.draw.polygon
    """
    r_coords = np.asarray(r_coords, dtype=float)
    c_coords = np.asarray(c_coords, dtype=float)
    n = len(r_coords)
    if n < 3:
        return np.array([], dtype=int), np.array([], dtype=int)

    r_min = int(np.floor(r_coords.min()))
    r_max = int(np.ceil(r_coords.max()))

    rr_out = []
    cc_out = []

    for r in range(r_min, r_max + 1):
        xs = []
        for i in range(n):
            r1, c1 = r_coords[i], c_coords[i]
            r2, c2 = r_coords[(i + 1) % n], c_coords[(i + 1) % n]
            if r1 == r2:
                continue
            # Only count an edge crossing the scanline once (half-open interval)
            if (r1 <= r < r2) or (r2 <= r < r1):
                t = (r - r1) / (r2 - r1)
                xs.append(c1 + t * (c2 - c1))

        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            c_start = int(round(xs[i]))
            c_end = int(round(xs[i + 1]))
            for c in range(c_start, c_end + 1):
                rr_out.append(r)
                cc_out.append(c)

    return np.array(rr_out, dtype=int), np.array(cc_out, dtype=int)


def _skeletonize(image):
    """
    Topological skeleton of a binary image via the Zhang-Suen thinning
    algorithm.

    Functionally replaces skimage.morphology.skeletonize.
    """
    img = (np.asarray(image) > 0).astype(np.uint8)
    rows, cols = img.shape

    changing = True
    while changing:
        changing = False
        for step in range(2):
            padded = np.pad(img, 1, mode='constant', constant_values=0)
            to_clear = []

            for i in range(1, rows + 1):
                for j in range(1, cols + 1):
                    if padded[i, j] == 0:
                        continue

                    p2 = padded[i - 1, j]
                    p3 = padded[i - 1, j + 1]
                    p4 = padded[i, j + 1]
                    p5 = padded[i + 1, j + 1]
                    p6 = padded[i + 1, j]
                    p7 = padded[i + 1, j - 1]
                    p8 = padded[i, j - 1]
                    p9 = padded[i - 1, j - 1]

                    neighbors = [p2, p3, p4, p5, p6, p7, p8, p9]
                    B = sum(neighbors)
                    if B < 2 or B > 6:
                        continue

                    seq = neighbors + [neighbors[0]]
                    A = sum(1 for k in range(8) if seq[k] == 0 and seq[k + 1] == 1)
                    if A != 1:
                        continue

                    if step == 0:
                        if p2 * p4 * p6 != 0:
                            continue
                        if p4 * p6 * p8 != 0:
                            continue
                    else:
                        if p2 * p4 * p8 != 0:
                            continue
                        if p2 * p6 * p8 != 0:
                            continue

                    to_clear.append((i - 1, j - 1))

            if to_clear:
                changing = True
                for (i, j) in to_clear:
                    img[i, j] = 0

    return img


def _skeleton_to_paths(skeleton):
    """
    Trace a thinned (1px-wide) binary skeleton into a list of polylines,
    each a list of (row, col) float coordinates.
    """
    pts = list(zip(*np.nonzero(skeleton)))
    pt_set = set(pts)
    if not pt_set:
        return []

    def neighbors(p):
        r, c = p
        out = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                q = (r + dr, c + dc)
                if q in pt_set:
                    out.append(q)
        return out

    neighbor_cache = {p: neighbors(p) for p in pt_set}
    degree = {p: len(neighbor_cache[p]) for p in pt_set}

    visited_edges = set()

    def edge_key(a, b):
        return (a, b) if a <= b else (b, a)

    def walk(start, nxt):
        path = [start, nxt]
        visited_edges.add(edge_key(start, nxt))
        prev, cur = start, nxt
        while True:
            if degree.get(cur, 0) != 2:
                break
            candidates = [q for q in neighbor_cache[cur] if q != prev]
            if not candidates:
                break
            following = candidates[0]
            ek = edge_key(cur, following)
            if ek in visited_edges:
                break
            visited_edges.add(ek)
            path.append(following)
            prev, cur = cur, following
            if cur == start:
                break
        return path

    paths = []

    # First trace all branches starting/ending at endpoints or junctions.
    for p in pts:
        if degree[p] == 2:
            continue
        for n in neighbor_cache[p]:
            if edge_key(p, n) in visited_edges:
                continue
            paths.append(walk(p, n))

    # Anything left over must be an isolated closed loop of degree-2 pixels.
    for p in pts:
        for n in neighbor_cache[p]:
            if edge_key(p, n) in visited_edges:
                continue
            paths.append(walk(p, n))

    return [[(float(r), float(c)) for r, c in path] for path in paths]


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


def FindBounds(radius: float, joints: list[tuple[int, int]], hei, large=True, small=True):
    if large:
        collObj = colls.Polygon(*joints)
        shapelyObj = colls.collToShapely(collObj)
        lgeObj = colls.shapelyToColl(shapelyObj.buffer(hei))
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
