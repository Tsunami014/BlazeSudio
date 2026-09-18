import math
import numpy as np
import BlazeSudio.collisions as colls

__all__ = [
    'MakeShape',
    'ShapeFormatError',
    'OverConstrainedError'
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


class ShapeFormatError(ValueError):
    """
    The shape is not in the correct format!
    """

class OverConstrainedError(ValueError):
    """
    The expression has been overly constrained and will not output a closed circle!
    """

class MakeShape:
    def __init__(self, width):
        self.joints = [(0, 0), (width, 0)]
        self.jointDists = [width]
        self.setAngs = [None]
        self.lastRadius = None

    @property
    def segments(self) -> list[tuple[tuple[int], tuple[int]]]:
        return [(self.joints[i], self.joints[i+1]) for i in range(len(self.joints)-1)]

    @property
    def collSegments(self) -> list[colls.Line]:
        return [colls.Line(self.joints[i], self.joints[i+1]) for i in range(len(self.joints)-1)]

    @property
    def width(self):
        return sum(self.jointDists)

    @width.setter
    def width(self, newWidth):
        d = 0
        for i in range(len(self.joints)-1):
            oldD = d
            x, y = self.joints[i+1][0]-self.joints[i][0], self.joints[i+1][1]-self.joints[i][1]
            d += math.sqrt(x**2+y**2)
            if d > newWidth:
                ang = math.degrees(math.atan2(y, x))-90
                newdist = newWidth-d-oldD
                self.joints = [*self.joints[:i], colls.rotate(self.joints[i], (self.joints[i][0], self.joints[i][1]+newdist), ang)]
                self.jointDists = [*self.jointDists[:i], newdist]
                self.setAngs = [*self.setAngs[:i], self.setAngs[i]]
                break
        else:
            x, y = self.joints[i+1][0]-self.joints[i][0], self.joints[i+1][1]-self.joints[i][1]
            ang = math.degrees(math.atan2(y, x))-90
            newdist = newWidth-d
            self.joints.append(colls.rotate(self.joints[-1], (self.joints[-1][0], self.joints[-1][1]+newdist), ang))
            self.jointDists.append(newdist)
            self.setAngs.append(None)

    def insert_straight(self, x):
        self.straighten()
        if self.joints[-1][0] < x < self.joints[0][0]:
            if x in (i[0] for i in self.joints):
                return False
            for idx in range(len(self.joints)-1):
                if self.joints[idx+1][0] < x:
                    self.joints.insert(idx+1, (x, self.joints[idx][1]))
                    self.setAngs.insert(idx+1, self.setAngs[idx])
                    self.recalculate_dists()
                    return True
        return False

    def recalculate_dists(self):
        prevj = None
        self.jointDists = []
        for j in self.joints:
            if prevj is None:
                prevj = j
                continue
            self.jointDists.append(math.sqrt((prevj[0]-j[0])**2+(prevj[1]-j[1])**2))
            prevj = j

    def recentre(self, newx, newy):
        centre = (
            sum(i[0] for i in self.joints)/len(self.joints),
            sum(i[1] for i in self.joints)/len(self.joints),
        )
        diff = (
            newx-centre[0],
            newy-centre[1],
        )
        self.joints = [
            (i[0]+diff[0], i[1]+diff[1]) for i in self.joints
        ]

    def _find_radius(self, epsilon=0.0000002, max_iters=1000, returnIterations=False):
        min_theta = 1.0 - epsilon
        max_theta = 1.0 + epsilon

        desired_angle = 360
        DA_ratio = desired_angle / 360

        sum_length = sum(self.jointDists)
        max_length = max(self.jointDists)

        min_radius = 0.5 * max_length
        max_radius = (0.5 * sum_length) / DA_ratio

        iterations = 0

        while True:
            sum_theta = 0.0
            iterations += 1
            radius = 0.5 * (min_radius + max_radius)

            for L in self.jointDists:
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

        self.lastRadius = radius

        if returnIterations:
            return radius, iterations

        return radius

    def makeShape(self): # Thanks SO MUCH to https://math.stackexchange.com/questions/1930607/maximum-area-enclosure-given-side-lengths
        # TODO: Multiple constraints in a row
        # TODO: Paralell constraints

        if len(self.jointDists) < 3:
            raise ShapeFormatError("Need at least three line lengths.")

        max_length = max(self.jointDists)
        sum_length = sum(self.jointDists)

        if max_length > sum_length - max_length:
            raise ShapeFormatError("Not a valid polygon; one of the line segments is too long.\n")

        radius = self._find_radius()

        startingi = 0
        got = 0
        for i in range(len(self.setAngs)):
            if self.setAngs[i] is not None:
                if got == 0:
                    startingi = i
                    got = 1
                elif got == 2:
                    raise OverConstrainedError(
                        'Cannot have multiple constraints not in a row!'
                    )
            elif got == 1:
                got = 2

        phi = -0.5 * theta(self.jointDists[startingi], radius)
        if got != 0:
            phi += math.radians(self.setAngs[startingi])

        x0 = radius * math.cos(phi)
        y0 = -radius * math.sin(phi)

        njs = []

        for i in range(len(self.jointDists)):
            L = self.jointDists[(i+startingi) % len(self.jointDists)]
            x = x0 - radius * math.cos(phi)
            y = y0 + radius * math.sin(phi)
            phi += theta(L, radius)
            njs.append((x, y))
        self.joints = [njs[i-startingi] for i in range(len(njs))] + [njs[-startingi]]

    def straighten(self):
        self.lastRadius = None
        for i in range(len(self.joints)-1):
            self.joints[i+1] = colls.rotate(self.joints[i], (self.joints[i][0], self.joints[i][1]+self.jointDists[i]), 90)

    def generateBounds(self, hei, large=True, main=True, small=True):
        if self.lastRadius is None:
            self.makeShape()

        collObj = None

        if large:
            collObj = colls.Polygon(*self.joints)
            shapelyObj = colls.collToShapely(collObj)
            lgeObj = colls.shapelyToColl(shapelyObj.buffer(hei))
        else:
            lgeObj = None

        if main:
            if collObj is None:
                collObj = colls.Polygon(*self.joints)
            mnObj = collObj
        else:
            mnObj = None

        if small:
            xs, ys = zip(*self.joints)
            minx, miny = min(xs), min(ys)
            image = np.zeros((int(max(xs)-minx)+1, int(max(ys)-miny)+1), dtype=np.uint8)
            rr, cc = _polygon_fill(np.array(xs)-minx, np.array(ys)-miny)
            image[rr, cc] = 1
            skeleton = _skeletonize(image)
            paths = _skeleton_to_paths(skeleton)
            smlObj = colls.Shapes(
                *[
                    colls.Line((float(u[0])+minx, float(u[1])+miny), (float(v[0])+minx, float(v[1])+miny)) for path in paths for u, v in zip(path[:-1], path[1:])
                ]
            )

        else:
            smlObj = None

        return lgeObj, mnObj, smlObj

    def delete(self, idx):
        self.lastRadius = None
        self.joints.pop(idx)
        if idx != len(self.joints):
            #self.jointDists[idx-1] += self.jointDists.pop(idx)
            self.jointDists.pop(idx)
            self.setAngs.pop(idx)

    def __iter__(self):
        return ((self.joints[i], self.joints[i+1]) for i in range(len(self.joints)-1))

    def __len__(self):
        return len(self.joints)-1

    def copy(self):
        s = MakeShape(10)
        s.joints = self.joints.copy()
        s.jointDists = self.jointDists.copy()
        s.setAngs = self.setAngs.copy()
        s.lastRadius = self.lastRadius
        return s
