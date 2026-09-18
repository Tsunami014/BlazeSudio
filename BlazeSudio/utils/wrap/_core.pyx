# distutils: language = c++
# cython: boundscheck=False, cdivision=True, initializedcheck=False
import math
import numpy as np
from libc.math cimport floor, ceil, lround, cos, sin, atan2, M_PI
from libc.stdlib cimport malloc, free, qsort
from libcpp.vector cimport vector
cimport numpy as cnp
cimport cython

cnp.import_array()


cpdef double theta(double L, double r):
    return 2.0 * math.asin(0.5 * L / r)


cdef int _cmp_double(const void* a, const void* b) noexcept nogil:
    cdef double da = (<double*> a)[0]
    cdef double db = (<double*> b)[0]
    if da < db:
        return -1
    elif da > db:
        return 1
    return 0


def _polygon_fill(r_coords, c_coords):
    """
    Rasterize a polygon given row (r) and column (c) vertex coordinates,
    returning (rr, cc) arrays of filled pixel coordinates.

    Equivalent in spirit to skimage.draw.polygon.
    """
    cdef cnp.ndarray[cnp.float64_t, ndim=1] r_arr = np.asarray(r_coords, dtype=np.float64)
    cdef cnp.ndarray[cnp.float64_t, ndim=1] c_arr = np.asarray(c_coords, dtype=np.float64)
    cdef Py_ssize_t n = r_arr.shape[0]
    if n < 3:
        return np.array([], dtype=int), np.array([], dtype=int)

    cdef double[:] r_v = r_arr
    cdef double[:] c_v = c_arr

    cdef Py_ssize_t r_min = <Py_ssize_t> floor(r_arr.min())
    cdef Py_ssize_t r_max = <Py_ssize_t> ceil(r_arr.max())

    cdef vector[long] rr_out
    cdef vector[long] cc_out

    cdef double* xs = <double*> malloc(n * sizeof(double))
    if xs == NULL:
        raise MemoryError()

    cdef Py_ssize_t r, i, c_start, c_end, c, xs_count
    cdef double r1, cc1, r2, cc2, t

    try:
        with nogil:
            for r in range(r_min, r_max + 1):
                xs_count = 0
                for i in range(n):
                    r1 = r_v[i]
                    cc1 = c_v[i]
                    r2 = r_v[(i + 1) % n]
                    cc2 = c_v[(i + 1) % n]
                    if r1 == r2:
                        continue
                    # Only count an edge crossing the scanline once (half-open interval)
                    if (r1 <= r < r2) or (r2 <= r < r1):
                        t = (r - r1) / (r2 - r1)
                        xs[xs_count] = cc1 + t * (cc2 - cc1)
                        xs_count += 1

                qsort(<void*> xs, <size_t> xs_count, sizeof(double), _cmp_double)

                i = 0
                while i + 1 < xs_count:
                    c_start = lround(xs[i])
                    c_end = lround(xs[i + 1])
                    for c in range(c_start, c_end + 1):
                        rr_out.push_back(r)
                        cc_out.push_back(c)
                    i += 2
    finally:
        free(xs)

    cdef Py_ssize_t m = rr_out.size()
    cdef cnp.ndarray[cnp.int64_t, ndim=1] rr = np.empty(m, dtype=np.int64)
    cdef cnp.ndarray[cnp.int64_t, ndim=1] cc = np.empty(m, dtype=np.int64)
    for i in range(m):
        rr[i] = rr_out[i]
        cc[i] = cc_out[i]
    return rr, cc


def _skeletonize(image):
    """
    Topological skeleton of a binary image via the Zhang-Suen thinning
    algorithm.

    Functionally replaces skimage.morphology.skeletonize.
    """
    cdef cnp.ndarray[cnp.uint8_t, ndim=2] img0 = (np.asarray(image) > 0).astype(np.uint8)
    cdef Py_ssize_t rows = img0.shape[0]
    cdef Py_ssize_t cols = img0.shape[1]

    cdef cnp.ndarray[cnp.uint8_t, ndim=2] padded_arr = np.zeros((rows + 2, cols + 2), dtype=np.uint8)
    padded_arr[1:rows + 1, 1:cols + 1] = img0
    cdef unsigned char[:, ::1] padded = padded_arr

    cdef bint changing = True
    cdef int step
    cdef Py_ssize_t i, j, k
    cdef int p2, p3, p4, p5, p6, p7, p8, p9, B, A
    cdef vector[Py_ssize_t] clear_i
    cdef vector[Py_ssize_t] clear_j

    while changing:
        changing = False
        for step in range(2):
            clear_i.clear()
            clear_j.clear()

            with nogil:
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

                        B = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
                        if B < 2 or B > 6:
                            continue

                        A = 0
                        if p2 == 0 and p3 == 1:  A += 1
                        if p3 == 0 and p4 == 1:  A += 1
                        if p4 == 0 and p5 == 1:  A += 1
                        if p5 == 0 and p6 == 1:  A += 1
                        if p6 == 0 and p7 == 1:  A += 1
                        if p7 == 0 and p8 == 1:  A += 1
                        if p8 == 0 and p9 == 1:  A += 1
                        if p9 == 0 and p2 == 1:  A += 1
                        if A != 1:  continue

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

                        clear_i.push_back(i)
                        clear_j.push_back(j)

            if clear_i.size() > 0:
                changing = True
                for k in range(<Py_ssize_t> clear_i.size()):
                    padded[clear_i[k], clear_j[k]] = 0

    return np.asarray(padded_arr)[1:rows + 1, 1:cols + 1].copy()


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


cpdef double c_direction(double x1, double y1, double x2, double y2):
    """Angle (radians) from (x1,y1) to (x2,y2)."""
    return atan2(y2 - y1, x2 - x1)


cpdef (double, double) c_rotate(double pivotx, double pivoty,
                                 double x, double y, double degrees):
    """Rotate (x,y) around (pivotx,pivoty) by `degrees`."""
    cdef double rad = degrees * M_PI / 180.0
    cdef double cos_a = cos(rad)
    cdef double sin_a = sin(rad)
    cdef double dx = x - pivotx
    cdef double dy = y - pivoty
    return (pivotx + dx * cos_a - dy * sin_a, pivoty + dx * sin_a + dy * cos_a)


def ray_polygon_closest_hit(double p1x, double p1y, double p2x, double p2y,
                             cnp.ndarray polygon, double tx, double ty):
    """
    Cast the infinite line through (p1,p2) against every edge of `polygon`
    (an Nx2 array-like of vertices) and return the intersection point
    closest to (tx,ty), or None if the line misses every edge.
    """
    cdef double[:, ::1] poly = np.ascontiguousarray(polygon, dtype=np.float64)
    cdef Py_ssize_t n = poly.shape[0]
    if n < 2:
        return None

    cdef Py_ssize_t i
    cdef double x3, y3, x4, y4, denom, t, u, hx, hy, d
    cdef bint found = False
    cdef double best_x = 0.0
    cdef double best_y = 0.0
    cdef double best_d = 1e300

    with nogil:
        for i in range(n):
            x3 = poly[i, 0]
            y3 = poly[i, 1]
            x4 = poly[(i + 1) % n, 0]
            y4 = poly[(i + 1) % n, 1]
            denom = (p1x - p2x) * (y3 - y4) - (p1y - p2y) * (x3 - x4)
            if -1e-12 < denom < 1e-12:
                continue
            t = ((p1x - x3) * (y3 - y4) - (p1y - y3) * (x3 - x4)) / denom
            u = ((p1x - x3) * (p1y - p2y) - (p1y - y3) * (p1x - p2x)) / denom
            if u < 0.0 or u > 1.0:
                continue
            hx = p1x + t * (p2x - p1x)
            hy = p1y + t * (p2y - p1y)
            d = (hx - tx) * (hx - tx) + (hy - ty) * (hy - ty)
            if d < best_d:
                best_d = d
                best_x = hx
                best_y = hy
                found = True

    if not found:
        return None
    return (best_x, best_y)


def closest_point_on_segments(double px, double py, cnp.ndarray segments):
    """
    segments: n segments, each [[ax,ay],[bx,by]].
    Returns the closest point on any segment to (px,py), or None if there are no segments.
    """
    if segments is None or len(segments) == 0:
        return None

    cdef double[:, :, ::1] segs = np.ascontiguousarray(segments, dtype=np.float64)
    cdef Py_ssize_t n = segs.shape[0]
    if n == 0:
        return None

    cdef Py_ssize_t i
    cdef double ax, ay, bx, by, dx, dy, length_sq, t, cx, cy, d
    cdef double best_x = 0.0
    cdef double best_y = 0.0
    cdef double best_d = 1e300

    with nogil:
        for i in range(n):
            ax = segs[i, 0, 0]
            ay = segs[i, 0, 1]
            bx = segs[i, 1, 0]
            by = segs[i, 1, 1]
            dx = bx - ax
            dy = by - ay
            length_sq = dx * dx + dy * dy
            if length_sq < 1e-12:
                cx = ax
                cy = ay
            else:
                t = ((px - ax) * dx + (py - ay) * dy) / length_sq
                if t < 0.0:
                    t = 0.0
                elif t > 1.0:
                    t = 1.0
                cx = ax + dx * t
                cy = ay + dy * t
            d = (cx - px) * (cx - px) + (cy - py) * (cy - py)
            if d < best_d:
                best_d = d
                best_x = cx
                best_y = cy

    return (best_x, best_y)



cdef inline (double, double) _normalize_c(double vx, double vy):
    cdef double length = math.hypot(vx, vy)
    if length == 0:
        return 0.0, 0.0
    return vx / length, vy / length


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


cdef inline void lerp2d(double p1x, double p1y, double p2x, double p2y,
                         double f, double *outx, double *outy) noexcept nogil:
    outx[0] = p1x + (p2x - p1x) * f
    outy[0] = p1y + (p2y - p1y) * f

cdef inline double dmin4(double a, double b, double c, double d) noexcept nogil:
    cdef double m = a
    if b < m:
        m = b
    if c < m:
        m = c
    if d < m:
        m = d
    return m

cdef inline double dmax4(double a, double b, double c, double d) noexcept nogil:
    cdef double m = a
    if b > m:
        m = b
    if c > m:
        m = c
    if d > m:
        m = d
    return m

cdef inline bint point_in_quad(double px, double py,
                                double x0, double y0,
                                double x1, double y1,
                                double x2, double y2,
                                double x3, double y3) noexcept nogil:
    """
    Point-in-convex-quad test via edge cross products
    """
    cdef double d0, d1, d2, d3
    d0 = (x1 - x0) * (py - y0) - (y1 - y0) * (px - x0)
    d1 = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
    d2 = (x3 - x2) * (py - y2) - (y3 - y2) * (px - x2)
    d3 = (x0 - x3) * (py - y3) - (y0 - y3) * (px - x3)
    return (d0 >= 0 and d1 >= 0 and d2 >= 0 and d3 >= 0) or \
           (d0 <= 0 and d1 <= 0 and d2 <= 0 and d3 <= 0)


# Improved from https://www.reddit.com/r/pygame/comments/z571pa/this_is_how_you_can_texture_a_polygon/
def draw_quad(unsigned char[:, :, ::1] surf_view not None,
              quad,
              unsigned char[:, :, ::1] img_view not None):
    cdef Py_ssize_t hei = img_view.shape[0]
    cdef Py_ssize_t wid = img_view.shape[1]
    cdef Py_ssize_t surf_h = surf_view.shape[0]
    cdef Py_ssize_t surf_w = surf_view.shape[1]

    cdef double q0x = quad[0][0]
    cdef double q0y = quad[0][1]
    cdef double q1x = quad[1][0]
    cdef double q1y = quad[1][1]
    cdef double q2x = quad[2][0]
    cdef double q2y = quad[2][1]
    cdef double q3x = quad[3][0]
    cdef double q3y = quad[3][1]

    cdef double inv_wid = 1.0 / wid
    cdef double inv_hei = 1.0 / hei

    cdef Py_ssize_t x, y, px, py_
    cdef double fy, fy1, fx, fx1
    cdef double b1x, b1y, b2x, b2y, c1x, c1y, c2x, c2y
    cdef double p0x, p0y, p1x, p1y, p2x, p2y, p3x, p3y
    cdef double minx, maxx, miny, maxy
    cdef Py_ssize_t ix0, ix1, iy0, iy1
    cdef unsigned char r, g, b, a
    cdef double alpha_f, inv_alpha_f
    cdef unsigned char *dst

    with nogil:
        for y in range(hei):
            fy = y * inv_hei
            fy1 = (y + 1) * inv_hei

            lerp2d(q1x, q1y, q2x, q2y, fy, &b1x, &b1y)
            lerp2d(q1x, q1y, q2x, q2y, fy1, &b2x, &b2y)
            lerp2d(q0x, q0y, q3x, q3y, fy, &c1x, &c1y)
            lerp2d(q0x, q0y, q3x, q3y, fy1, &c2x, &c2y)

            for x in range(wid):
                fx = x * inv_wid
                fx1 = (x + 1) * inv_wid

                lerp2d(c1x, c1y, b1x, b1y, fx, &p0x, &p0y)
                lerp2d(c1x, c1y, b1x, b1y, fx1, &p1x, &p1y)
                lerp2d(c2x, c2y, b2x, b2y, fx1, &p2x, &p2y)
                lerp2d(c2x, c2y, b2x, b2y, fx, &p3x, &p3y)

                r = img_view[y, x, 0]
                g = img_view[y, x, 1]
                b = img_view[y, x, 2]
                a = img_view[y, x, 3]

                if a == 0:
                    continue

                minx = dmin4(p0x, p1x, p2x, p3x)
                maxx = dmax4(p0x, p1x, p2x, p3x)
                miny = dmin4(p0y, p1y, p2y, p3y)
                maxy = dmax4(p0y, p1y, p2y, p3y)

                ix0 = <Py_ssize_t> floor(minx)
                ix1 = <Py_ssize_t> ceil(maxx)
                iy0 = <Py_ssize_t> floor(miny)
                iy1 = <Py_ssize_t> ceil(maxy)

                if ix0 < 0:
                    ix0 = 0
                if iy0 < 0:
                    iy0 = 0
                if ix1 > surf_w:
                    ix1 = surf_w
                if iy1 > surf_h:
                    iy1 = surf_h

                alpha_f = a / 255.0
                inv_alpha_f = 1.0 - alpha_f

                for py_ in range(iy0, iy1):
                    for px in range(ix0, ix1):
                        if point_in_quad(px + 0.5, py_ + 0.5,
                                          p0x, p0y, p1x, p1y,
                                          p2x, p2y, p3x, p3y):
                            dst = &surf_view[py_, px, 0]
                            if a == 255:
                                dst[0] = r
                                dst[1] = g
                                dst[2] = b
                                dst[3] = 255
                            else:
                                dst[0] = <unsigned char>(r * alpha_f + dst[0] * inv_alpha_f)
                                dst[1] = <unsigned char>(g * alpha_f + dst[1] * inv_alpha_f)
                                dst[2] = <unsigned char>(b * alpha_f + dst[2] * inv_alpha_f)
                                dst[3] = <unsigned char>(255 * alpha_f + dst[3] * inv_alpha_f)
