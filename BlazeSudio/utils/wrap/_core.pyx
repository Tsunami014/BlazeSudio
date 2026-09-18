# cython: boundscheck=False, cdivision=True
import math
import numpy as np
cimport numpy as cnp
cimport cython

cnp.import_array()


cpdef double theta(double L, double r):
    return 2.0 * math.asin(0.5 * L / r)

cpdef double d_theta(double L, double r):
    cdef double r2 = r * r
    return -2.0 * L / (r2 * math.sqrt(4.0 - L * L / r2))


def _polygon_fill(r_coords, c_coords):
    """
    Rasterize a polygon given row (r) and column (c) vertex coordinates,
    returning (rr, cc) arrays of filled pixel coordinates.

    Equivalent in spirit to skimage.draw.polygon
    """
    cdef cnp.ndarray[cnp.float64_t, ndim=1] r_arr = np.asarray(r_coords, dtype=np.float64)
    cdef cnp.ndarray[cnp.float64_t, ndim=1] c_arr = np.asarray(c_coords, dtype=np.float64)
    cdef Py_ssize_t n = r_arr.shape[0]
    if n < 3:
        return np.array([], dtype=int), np.array([], dtype=int)

    cdef Py_ssize_t r_min = int(np.floor(r_arr.min()))
    cdef Py_ssize_t r_max = int(np.ceil(r_arr.max()))

    cdef list rr_out = []
    cdef list cc_out = []

    cdef Py_ssize_t r, i, c_start, c_end, c
    cdef double r1, cc1, r2, cc2, t
    cdef list xs

    for r in range(r_min, r_max + 1):
        xs = []
        for i in range(n):
            r1 = r_arr[i]
            cc1 = c_arr[i]
            r2 = r_arr[(i + 1) % n]
            cc2 = c_arr[(i + 1) % n]
            if r1 == r2:
                continue
            # Only count an edge crossing the scanline once (half-open interval)
            if (r1 <= r < r2) or (r2 <= r < r1):
                t = (r - r1) / (r2 - r1)
                xs.append(cc1 + t * (cc2 - cc1))

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
    cdef cnp.ndarray[cnp.uint8_t, ndim=2] img = (np.asarray(image) > 0).astype(np.uint8)
    cdef Py_ssize_t rows = img.shape[0]
    cdef Py_ssize_t cols = img.shape[1]

    cdef bint changing = True
    cdef int step
    cdef Py_ssize_t i, j
    cdef cnp.ndarray[cnp.uint8_t, ndim=2] padded
    cdef int p2, p3, p4, p5, p6, p7, p8, p9
    cdef int B, A, k
    cdef list to_clear

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
                    B = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
                    if B < 2 or B > 6:
                        continue

                    seq = neighbors + [neighbors[0]]
                    A = 0
                    for k in range(8):
                        if seq[k] == 0 and seq[k + 1] == 1:
                            A += 1
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


cdef inline (double, double) _normalize_c(double vx, double vy):
    cdef double length = math.hypot(vx, vy)
    if length == 0:
        return 0.0, 0.0
    return vx / length, vy / length


def _normalize(vx, vy):
    return _normalize_c(vx, vy)


def _line_intersect(p1, p2, p3, p4):
    """Intersection point of infinite lines through (p1,p2) and (p3,p4), or None if parallel."""
    cdef double x1, y1, x2, y2, x3, y3, x4, y4, denom, px, py
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-12:
        return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return (px, py)


def _polygon_buffer(points, distance, arc_segments=8):
    points = list(points)

    while len(points) > 1 and math.hypot(
        points[0][0] - points[-1][0], points[0][1] - points[-1][1]
    ) < 1e-9:
        points.pop()

    cdef list deduped = []
    cdef double px, py
    for px, py in points:
        if deduped:
            lx, ly = deduped[-1]
            if math.hypot(px - lx, py - ly) < 1e-9:
                continue
        deduped.append((px, py))
    # re-check wrap seam after interior dedup
    while len(deduped) > 1 and math.hypot(
        deduped[0][0] - deduped[-1][0], deduped[0][1] - deduped[-1][1]
    ) < 1e-9:
        deduped.pop()
    points = deduped

    cdef Py_ssize_t n = len(points)
    if n < 3:
        return points

    cdef Py_ssize_t i
    cdef double area2 = 0.0
    cdef double x1, y1, x2, y2, x3, y3
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area2 += x1 * y2 - x2 * y1
    if area2 < 0:
        points = list(reversed(points))

    # Offset every edge outward by distance along its normal.
    cdef list offset_edges = []
    cdef double dx, dy, nx, ny
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        dx, dy = _normalize_c(x2 - x1, y2 - y1)
        # Outward normal for a CCW-wound polygon.
        nx, ny = dy, -dx
        offset_edges.append((
            (x1 + nx * distance, y1 + ny * distance),
            (x2 + nx * distance, y2 + ny * distance),
        ))

    cdef list result = []
    cdef double v1x, v1y, v2x, v2y, cross, dot
    cdef double cx, cy, start_ang, end_ang, a, sweep_ang
    cdef Py_ssize_t steps, s

    for i in range(n):
        prev_edge = offset_edges[(i - 1) % n]
        curr_edge = offset_edges[i]

        x1, y1 = points[(i - 1) % n]
        x2, y2 = points[i]
        x3, y3 = points[(i + 1) % n]
        v1x, v1y = _normalize_c(x2 - x1, y2 - y1)
        v2x, v2y = _normalize_c(x3 - x2, y3 - y2)
        cross = v1x * v2y - v1y * v2x
        dot = v1x * v2x + v1y * v2y

        if cross >= 0:
            # Convex vertex: round the corner with a small arc.
            start_pt = prev_edge[1]
            end_pt = curr_edge[0]
            cx, cy = x2, y2

            sweep_ang = math.atan2(cross, dot)
            if sweep_ang < 0:
                sweep_ang += 2.0 * math.pi
            start_ang = math.atan2(start_pt[1] - cy, start_pt[0] - cx)
            end_ang = start_ang + sweep_ang

            steps = max(1, int(round(arc_segments * sweep_ang / (2 * math.pi))) + 1)
            for s in range(steps + 1):
                a = start_ang + (end_ang - start_ang) * s / steps
                result.append((cx + abs(distance) * math.cos(a), cy + abs(distance) * math.sin(a)))
        else:
            # Reflex vertex: miter join via line intersection.
            ip = _line_intersect(prev_edge[0], prev_edge[1], curr_edge[0], curr_edge[1])
            result.append(ip if ip is not None else curr_edge[0])

    return result
