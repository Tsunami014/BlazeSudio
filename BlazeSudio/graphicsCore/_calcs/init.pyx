# cython: boundscheck=False, wraparound=False, nonecheck=False, cdivision=True
import numpy as np
from libc.stdlib cimport malloc, free
cimport numpy as cnp
__cimport_types__ = [cnp.ndarray]

cdef inline long clip(long v, long lo, long hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


cpdef drawLine(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr,
        double[:] p1,
        double[:] p2,
        double thickness,
        cnp.ndarray[cnp.uint8_t, ndim=1] col,
        crop):
    cdef long x = <long>p1[0]
    cdef long y = <long>p1[1]
    cdef long x1 = <long>p2[0]
    cdef long y1 = <long>p2[1]
    cdef long half = <long>(thickness) >> 1

    cdef long dx = abs(x1 - x)
    cdef long dy = abs(y1 - y)
    cdef long err
    cdef long sx, sy
    cdef long ys, ye, xs, xe
    cdef long i

    cdef unsigned char rcol = col[0]
    cdef unsigned char gcol = col[1]
    cdef unsigned char bcol = col[2]
    cdef unsigned char acol = col[3]

    cdef long cLeft = <long>crop[0]
    cdef long cTop = <long>crop[1]
    cdef long cRight = <long>crop[2]
    cdef long cBot = <long>crop[3]

    if dx > dy:
        if x > x1:
            x, x1 = x1, x
            y, y1 = y1, y
        sy = 1 if y < y1 else -1
        err = dx // 2
        while x <= x1:
            if x >= cLeft and x <= cRight:
                ys = max(y - half, cTop)
                ye = min(y + half + 1, cBot)
                xs = min(max(x, cLeft), cRight)

                if ys < ye:
                    for i in range(ys, ye):
                        arr[i, xs, 0] = rcol
                        arr[i, xs, 1] = gcol
                        arr[i, xs, 2] = bcol
                        arr[i, xs, 3] = acol

            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += 1
    else:
        if y > y1:
            x, x1 = x1, x
            y, y1 = y1, y
        sx = 1 if x < x1 else -1
        err = dy // 2
        while y <= y1:
            if y >= cTop and y <= cBot:
                xs = max(x - half, cLeft)
                xe = min(x + half + 1, cRight)
                ys = min(max(y, cTop), cBot)

                if xs < xe:
                    for i in range(xs, xe):
                        arr[ys, i, 0] = rcol
                        arr[ys, i, 1] = gcol
                        arr[ys, i, 2] = bcol
                        arr[ys, i, 3] = acol

            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += 1


cdef void fillPolygon(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr,
        double[:, :] points,
        cnp.ndarray[cnp.uint8_t, ndim=1] col,
        crop):
    cdef long n = points.shape[0]
    if n < 3:
        return

    cdef unsigned char rcol = col[0]
    cdef unsigned char gcol = col[1]
    cdef unsigned char bcol = col[2]
    cdef unsigned char acol = col[3]

    cdef long cLeft = <long>crop[0]
    cdef long cTop = <long>crop[1]
    cdef long cRight = <long>crop[2]
    cdef long cBot = <long>crop[3]

    cdef long i, j, y, x, k, m
    cdef long yMin = cBot
    cdef long yMax = cTop
    cdef double yi, yj, xi, xj, t, xint_d
    cdef long xint
    cdef long* inters = <long*>malloc(n * sizeof(long))
    if inters == NULL:
        return

    # polygon bbox in y, clipped to crop
    for i in range(n):
        y = <long>points[i, 1]
        if y < yMin: yMin = y
        if y > yMax: yMax = y

    if yMin < cTop: yMin = cTop
    if yMax > cBot: yMax = cBot

    cdef unsigned char *cell

    # scanline fill (even-odd rule)
    for y in range(yMin, yMax + 1):
        k = 0
        for i in range(n):
            j = (i + 1) % n
            yi = points[i, 1]
            yj = points[j, 1]

            # include edges crossing this scanline; avoids double-count at vertices
            if ((yi <= y and y < yj) or (yj <= y and y < yi)):
                xi = points[i, 0]
                xj = points[j, 0]
                t = (y - yi) / (yj - yi)
                xint_d = xi + t * (xj - xi)
                xint = <long>xint_d
                if xint < cLeft:
                    xint = cLeft
                elif xint > cRight:
                    xint = cRight
                inters[k] = xint
                k += 1

        # insertion sort intersections
        for i in range(1, k):
            x = inters[i]
            m = i - 1
            while m >= 0 and inters[m] > x:
                inters[m + 1] = inters[m]
                m -= 1
            inters[m + 1] = x

        # fill pairs
        i = 0
        while i + 1 < k:
            xi = inters[i]
            xj = inters[i + 1]
            if xi < cLeft: xi = cLeft
            if xj > cRight: xj = cRight
            for x in range(<long>xi, <long>xj + 1):
                cell = &arr[y, x, 0]
                cell[0] = rcol
                cell[1] = gcol
                cell[2] = bcol
                cell[3] = acol
            i += 2

    free(inters)


cpdef drawPolyLine(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr,
        double[:, :] points,
        double thickness,
        cnp.ndarray[cnp.uint8_t, ndim=1] col,
        crop, bool round):
    cdef long n = len(points)
    if n < 2:
        return
    if thickness <= 0:
        fillPolygon(arr, points, col, crop)
        return

    cdef long ht = <long>(thickness // 2)
    if round:
        for i in range(n):
            drawCirc(arr, points[i], ht, 0, col, crop)
    if n == 2:
        drawLine(arr, points[0], points[1], thickness, col, crop)
        return
    p1 = points[0]
    for i in range(1, n):
        p2 = points[i]
        drawLine(arr, p1, p2, thickness, col, crop)
        p1 = p2
    drawLine(arr, p1, points[0], thickness, col, crop)


cdef _fill(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr,
        long fromy, long toy, long fromx, long tox,
        long rcol, long gcol, long bcol, long acol):
    cdef long y, x
    cdef long diff = tox - fromx
    cdef unsigned char *cell
    for y in range(fromy, toy):
        cell = &arr[y, fromx, 0]
        for x in range(diff):
            cell[0] = rcol
            cell[1] = gcol
            cell[2] = bcol
            cell[3] = acol
            cell += 4

cpdef drawRect(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr,
        double[:] pos,
        double[:] sze,
        double thickness,
        double round,
        cnp.ndarray[cnp.uint8_t, ndim=1] col,
        crop):
    cdef long t = <long>thickness

    cdef long x0 = <long>pos[0]
    cdef long y0 = <long>pos[1]
    cdef long x1 = x0 + <long>sze[0]
    cdef long y1 = y0 + <long>sze[1]

    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0

    cdef long cLeft = <long>crop[0]
    cdef long cTop = <long>crop[1]
    cdef long cRight = <long>crop[2]
    cdef long cBot = <long>crop[3]

    cdef long w = x1 - x0
    cdef long h = y1 - y0

    cdef long hwid = <long>(w * 0.5)
    cdef long hhei = <long>(h * 0.5)
    cdef long r = <long>round
    if r > hwid:
        r = hwid
    if r > hhei:
        r = hhei
    if r < 0:
        r = 0

    cdef unsigned char rcol = col[0]
    cdef unsigned char gcol = col[1]
    cdef unsigned char bcol = col[2]
    cdef unsigned char acol = col[3]

    cdef long x, y

    if t <= 0:
        if r == 0:
            _fill(arr,
                clip(y0, cTop, cBot), clip(y1, cTop, cBot),
                clip(x0, cLeft, cRight), clip(x1, cLeft, cRight),
                rcol, gcol, bcol, acol)
            return

        # Rounded fill (top/bottom strips + middle)
        _fill(arr,
            clip(y0 + r, cTop, cBot), clip(y1 - r, cTop, cBot),
            clip(x0, cLeft, cRight), clip(x1, cLeft, cRight),
            rcol, gcol, bcol, acol)
        _fill(arr,
            clip(y0, cTop, cBot), clip(y1, cTop, cBot),
            clip(x0 + r, cLeft, cRight), clip(x1 - r, cLeft, cRight),
            rcol, gcol, bcol, acol)
    else:
        _fill(arr, # Top
            clip(y0, cTop, cBot), clip(y0 + t, cTop, cBot),
            x0+r, x1-r, rcol, gcol, bcol, acol)
        _fill(arr, # Bottom
            clip(y1 - t, cTop, cBot), clip(y1, cTop, cBot),
            x0+r, x1-r, rcol, gcol, bcol, acol)
        _fill(arr, y0+r, y1-r, # Left
            clip(x0, cLeft, cRight), clip(x0 + t, cLeft, cRight),
            rcol, gcol, bcol, acol)
        _fill(arr, y0+r, y1-r, # Right
            clip(x1 - t, cLeft, cRight), clip(x1, cLeft, cRight),
            rcol, gcol, bcol, acol)

    cdef long outer, inner, off
    cdef long cx, cy, xs, xe, ys, ye
    cdef long dx, dy, d2
    if r > 1:
        outer = r*r
        if t > 0:
            inner = r - t
            if inner < 0:
                inner = 0
            else:
                inner *= inner
        else:
            inner = 0

        off = 0 if t > 0 else 1

        # TL, TR, BL, BR
        corners = [
            (x0 + r - off, y0 + r - 1, x0, x0+r, y0, y0+r),
            (x1 - r,       y0 + r - 1, x1-r, x1, y0, y0+r),
            (x0 + r - off, y1 - r - 1 + off, x0, x0+r, y1-r, y1),
            (x1 - r,       y1 - r - 1 + off, x1-r, x1, y1-r, y1)
        ]

        for cx, cy, xs, xe, ys, ye in corners:
            xs = clip(xs, cLeft, cRight)
            xe = clip(xe, cLeft, cRight)
            ys = clip(ys, cTop, cBot)
            ye = clip(ye, cTop, cBot)

            for y in range(ys, ye):
                if y < cTop or y > cBot:
                    continue
                dy = y - cy
                for x in range(xs, xe):
                    if x < cLeft or x > cRight:
                        continue
                    dx = x - cx
                    d2 = dx*dx + dy*dy
                    if inner <= d2 < outer:
                        arr[y, x, 0] = rcol
                        arr[y, x, 1] = gcol
                        arr[y, x, 2] = bcol
                        arr[y, x, 3] = acol


cpdef drawCirc(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr,
        double[:] pos,
        double radius,
        double thickness,
        cnp.ndarray[cnp.uint8_t, ndim=1] col,
        crop):
    cdef long r = <long>radius
    cdef long x = <long>pos[0]
    cdef long y = <long>pos[1]

    cdef long y0 = max(y - r - 1, <long>crop[1])
    cdef long y1 = min(y + r + 1, <long>crop[3])
    cdef long x0 = max(x - r - 1, <long>crop[0])
    cdef long x1 = min(x + r + 1, <long>crop[2])
    if y0 >= y1 or x0 >= x1:
        return

    cdef long outrad2 = r * r
    cdef long innrad2
    if thickness == 0:
        innrad2 = 0
    else:
        innrad2 = max(r - <long>thickness, 0)
        innrad2 *= innrad2

    cdef unsigned char rcol = col[0]
    cdef unsigned char gcol = col[1]
    cdef unsigned char bcol = col[2]
    cdef unsigned char acol = col[3]

    cdef long xx, yy
    cdef long dx, dy
    cdef long dist_sq
    for yy in range(y0, y1):
        dy = yy - y
        for xx in range(x0, x1):
            dx = xx - x
            dist_sq = dx*dx + dy*dy

            if innrad2 <= dist_sq <= outrad2:
                arr[yy, xx, 0] = rcol
                arr[yy, xx, 1] = gcol
                arr[yy, xx, 2] = bcol
                arr[yy, xx, 3] = acol


cpdef drawElipse(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr,
        double[:] pos,
        double xradius,
        double yradius,
        double rotation,
        double thickness,
        cnp.ndarray[cnp.uint8_t, ndim=1] col,
        crop):
    cdef long xrad = <long>xradius
    cdef long yrad = <long>yradius
    cdef long x = <long>pos[0]
    cdef long y = <long>pos[1]

    cdef long t
    if thickness >= min(xrad, yrad):
        t = 0
    else:
        t = <long>(thickness / 2)

    # Bounding box
    cdef long x_min = max(x - xrad- 1 - t, <long>crop[0])
    cdef long x_max = min(x + xrad+ 1 + t, <long>crop[2])
    cdef long y_min = max(y - yrad- 1 - t, <long>crop[1])
    cdef long y_max = min(y + yrad+ 1 + t, <long>crop[3])
    if y_min >= y_max or x_min >= x_max:
        return

    # Rotation
    cdef double cos_t = np.cos(rotation)
    cdef double sin_t = np.sin(rotation)

    cdef long xx, yy
    cdef double dx, dy
    cdef double xr, yr
    cdef double v_outer, v_inner

    cdef unsigned char rcol = col[0]
    cdef unsigned char gcol = col[1]
    cdef unsigned char bcol = col[2]
    cdef unsigned char acol = col[3]

    if t == 0:
        invxr = 1.0 / (xrad * xrad)
        invyr = 1.0 / (yrad * yrad)
        for yy in range(y_min, y_max):
            dy = yy - y
            for xx in range(x_min, x_max):
                dx = xx - x

                xr = dx * cos_t + dy * sin_t
                yr = -dx * sin_t + dy * cos_t

                if xr * xr * invxr + yr * yr * invyr <= 1.0:
                    arr[yy, xx, 0] = rcol
                    arr[yy, xx, 1] = gcol
                    arr[yy, xx, 2] = bcol
                    arr[yy, xx, 3] = acol
    else:
        inv_right = 1.0 / ((xrad + t) * (xrad + t))
        inv_bot = 1.0 / ((yrad + t) * (yrad + t))
        inv_left = 1.0 / ((xrad - t) * (xrad - t))
        inv_top = 1.0 / ((yrad - t) * (yrad - t))

        for yy in range(y_min, y_max):
            dy = yy - y
            for xx in range(x_min, x_max):
                dx = xx - x

                xr = dx * cos_t + dy * sin_t
                yr = -dx * sin_t + dy * cos_t

                v_outer = xr * xr * inv_right + yr * yr * inv_bot
                if v_outer <= 1.0:
                    v_inner = xr * xr * inv_left + yr * yr * inv_top
                    if v_inner > 1.0:
                        arr[yy, xx, 0] = rcol
                        arr[yy, xx, 1] = gcol
                        arr[yy, xx, 2] = bcol
                        arr[yy, xx, 3] = acol

