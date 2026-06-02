# cython: boundscheck=False, wraparound=False, nonecheck=False, cdivision=True
import numpy as np
cimport numpy as cnp
from libc.stdlib cimport malloc, free
from libc.string cimport memset
from libc.stdint cimport uint32_t
from cython.parallel import prange
__cimport_types__ = [cnp.ndarray]

cdef unsigned int THRESH = 300

cpdef fill_arr(cnp.ndarray[cnp.uint8_t, ndim=3] arr,
               cnp.ndarray[cnp.uint8_t, ndim=1] col):
    cdef unsigned char rcol = col[0]
    cdef unsigned char gcol = col[1]
    cdef unsigned char bcol = col[2]
    cdef unsigned char *p = &arr[0,0,0]
    if rcol == gcol and gcol == bcol:
        memset(p, rcol, <size_t>arr.size)
        return
    cdef long n = arr.shape[0] * arr.shape[1]
    cdef uint32_t color32 = (rcol) | (gcol << 8) | (bcol << 16) | (255 << 24)
    cdef uint32_t *p32 = <uint32_t*> p
    cdef long i
    for i in prange(n, nogil=True, use_threads_if=n > THRESH):
        p32[i] = color32

cdef inline long clip(long v, long lo, long hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


cdef void fillPolygon(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr_orig,
        double[:, :] points,
        cnp.ndarray[cnp.uint8_t, ndim=1] col,
        crop):
    cdef long n = points.shape[0]
    if n < 3:
        return

    cdef unsigned char acol = col[3]
    if acol == 0:
        return
    cdef unsigned char inva = 255 - acol
    cdef unsigned long rcol = col[0]
    cdef unsigned long racol = col[0]*acol
    cdef unsigned long gcol = col[1]
    cdef unsigned long gacol = col[1]*acol
    cdef unsigned long bcol = col[2]
    cdef unsigned long bacol = col[2]*acol

    cdef unsigned char[:, :, ::1] arr = arr_orig

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
        for i in range(0, k-1, 2):#, nogil=True):
            xi = inters[i]
            xj = inters[i + 1]
            if xi < cLeft: xi = cLeft
            if xj > cRight: xj = cRight
            for x in range(<long>xi, <long>xj + 1):
                cell = &arr[y, x, 0]
                if acol == 255:
                    cell[0] = <unsigned char>(rcol)
                    cell[1] = <unsigned char>(gcol)
                    cell[2] = <unsigned char>(bcol)
                    cell[3] = 255
                else:
                    cell[0] = <unsigned char>((racol + cell[0]*inva) >> 8)
                    cell[1] = <unsigned char>((gacol + cell[1]*inva) >> 8)
                    cell[2] = <unsigned char>((bacol + cell[2]*inva) >> 8)
                    oa = acol + cell[3]
                    if oa > 255:
                        oa = 255
                        cell[3] = <unsigned char>(oa)
    free(inters)


cpdef drawLinePoly(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr,
        double[:] p1,
        double[:] p2,
        double thickness,
        cnp.ndarray[cnp.uint8_t, ndim=1] col,
        crop):
    cdef double dx = p2[0] - p1[0]
    cdef double dy = p2[1] - p1[1]
    cdef double length = np.sqrt(dx*dx + dy*dy)

    if length == 0:
        return

    cdef double px = -dy / length
    cdef double py = dx / length
    cdef double half = thickness / 2.0

    # Create the 4 corners of the thick line
    cdef double[:, :] poly = np.zeros((4, 2), dtype=np.float64)
    poly[0, 0] = p1[0] + px * half
    poly[0, 1] = p1[1] + py * half
    poly[1, 0] = p2[0] + px * half
    poly[1, 1] = p2[1] + py * half
    poly[2, 0] = p2[0] - px * half
    poly[2, 1] = p2[1] - py * half
    poly[3, 0] = p1[0] - px * half
    poly[3, 1] = p1[1] - py * half

    fillPolygon(arr, poly, col, crop)

cpdef drawLine(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr_orig,
        double[:] p1,
        double[:] p2,
        double thickness,
        cnp.ndarray[cnp.uint8_t, ndim=1] col,
        crop):
    cdef unsigned char acol = col[3]
    if acol == 0:
        return

    if thickness > 1:
        drawLinePoly(arr_orig, p1, p2, thickness, col, crop)
        return

    cdef unsigned char[:, :, ::1] arr = arr_orig

    cdef unsigned char inva = 255 - acol
    cdef unsigned long rcol = col[0]
    cdef unsigned long racol = col[0]*acol
    cdef unsigned long gcol = col[1]
    cdef unsigned long gacol = col[1]*acol
    cdef unsigned long bcol = col[2]
    cdef unsigned long bacol = col[2]*acol

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
    cdef long i, oa

    cdef long cLeft = <long>crop[0]
    cdef long cTop = <long>crop[1]
    cdef long cRight = <long>crop[2]
    cdef long cBot = <long>crop[3]

    cdef unsigned char *cell
    cdef long steps
    if dx > dy:
        if x > x1:
            x, x1 = x1, x
            y, y1 = y1, y
        sy = 1 if y < y1 else -1
        err = dx // 2
        steps = dx + 1
        for _ in range(steps):
            if x >= cLeft and x <= cRight:
                ys = max(y - half, cTop)
                ye = min(y + half + 1, cBot)
                xs = min(max(x, cLeft), cRight)

                if ys < ye:
                    for i in range(ys, ye):
                        cell = &arr[i, xs, 0]
                        if acol == 255:
                            cell[0] = <unsigned char>(rcol)
                            cell[1] = <unsigned char>(gcol)
                            cell[2] = <unsigned char>(bcol)
                            cell[3] = 255
                        else:
                            cell[0] = <unsigned char>((racol + cell[0]*inva) >> 8)
                            cell[1] = <unsigned char>((gacol + cell[1]*inva) >> 8)
                            cell[2] = <unsigned char>((bacol + cell[2]*inva) >> 8)
                            oa = acol + cell[3]
                            if oa > 255:
                                oa = 255
                                cell[3] = <unsigned char>(oa)
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
        steps = dy + 1
        for _ in range(steps):
            if y >= cTop and y <= cBot:
                xs = max(x - half, cLeft)
                xe = min(x + half + 1, cRight)
                ys = min(max(y, cTop), cBot)

                if xs < xe:
                    for i in range(xs, xe):
                        cell = &arr[ys, i, 0]
                        if acol == 255:
                            cell[0] = <unsigned char>(rcol)
                            cell[1] = <unsigned char>(gcol)
                            cell[2] = <unsigned char>(bcol)
                            cell[3] = 255
                        else:
                            cell[0] = <unsigned char>((racol + cell[0]*inva) >> 8)
                            cell[1] = <unsigned char>((gacol + cell[1]*inva) >> 8)
                            cell[2] = <unsigned char>((bacol + cell[2]*inva) >> 8)
                            oa = acol + cell[3]
                            if oa > 255:
                                oa = 255
                                cell[3] = <unsigned char>(oa)
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += 1


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
        long rcol, long racol, long gcol, long gacol, long bcol, long bacol, long acol, long inva):
    cdef long y, x, oa
    cdef unsigned char *cell
    for y in prange(fromy, toy, use_threads_if=(toy-fromy) > THRESH, nogil=True):
        for x in range(fromx, tox):
            cell = &arr[y, x, 0]
            if acol == 255:
                cell[0] = <unsigned char>(rcol)
                cell[1] = <unsigned char>(gcol)
                cell[2] = <unsigned char>(bcol)
                cell[3] = 255
            else:
                cell[0] = <unsigned char>((racol + cell[0]*inva) >> 8)
                cell[1] = <unsigned char>((gacol + cell[1]*inva) >> 8)
                cell[2] = <unsigned char>((bacol + cell[2]*inva) >> 8)
                oa = acol + cell[3]
                if oa > 255:
                    oa = 255
                    cell[3] = <unsigned char>(oa)

cpdef drawRect(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr,
        double[:] pos,
        double[:] sze,
        double thickness,
        double round,
        cnp.ndarray[cnp.uint8_t, ndim=1] col,
        crop):
    cdef unsigned char acol = col[3]
    if acol == 0:
        return
    cdef unsigned char inva = 255 - acol
    cdef unsigned char rcol = col[0]
    cdef unsigned long racol = col[0]*acol
    cdef unsigned char gcol = col[1]
    cdef unsigned long gacol = col[1]*acol
    cdef unsigned char bcol = col[2]
    cdef unsigned long bacol = col[2]*acol

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

    cdef long x, y

    if t <= 0:
        if r == 0:
            _fill(arr,
                clip(y0, cTop, cBot), clip(y1, cTop, cBot),
                clip(x0, cLeft, cRight), clip(x1, cLeft, cRight),
                rcol, racol, gcol, gacol, bcol, bacol, acol, inva)
            return

        # Rounded fill (Middle block spanning full width)
        _fill(arr,
            clip(y0 + r, cTop, cBot), clip(y1 - r, cTop, cBot),
            clip(x0, cLeft, cRight), clip(x1, cLeft, cRight),
            rcol, racol, gcol, gacol, bcol, bacol, acol, inva)
            
        # Top strip (between corners)
        _fill(arr,
            clip(y0, cTop, cBot), clip(y0 + r, cTop, cBot),
            clip(x0 + r, cLeft, cRight), clip(x1 - r, cLeft, cRight),
            rcol, racol, gcol, gacol, bcol, bacol, acol, inva)
            
        # Bottom strip (between corners)
        _fill(arr,
            clip(y1 - r, cTop, cBot), clip(y1, cTop, cBot),
            clip(x0 + r, cLeft, cRight), clip(x1 - r, cLeft, cRight),
            rcol, racol, gcol, gacol, bcol, bacol, acol, inva)
    else:
        _fill(arr, # Top
            clip(y0, cTop, cBot), clip(y0 + t, cTop, cBot), x0+r, x1-r,
            rcol, racol, gcol, gacol, bcol, bacol, acol, inva)
        _fill(arr, # Bottom
            clip(y1 - t, cTop, cBot), clip(y1, cTop, cBot), x0+r, x1-r,
            rcol, racol, gcol, gacol, bcol, bacol, acol, inva)
        _fill(arr, y0+r, y1-r, # Left
            clip(x0, cLeft, cRight), clip(x0 + t, cLeft, cRight),
            rcol, racol, gcol, gacol, bcol, bacol, acol, inva)
        _fill(arr, y0+r, y1-r, # Right
            clip(x1 - t, cLeft, cRight), clip(x1, cLeft, cRight),
            rcol, racol, gcol, gacol, bcol, bacol, acol, inva)

    cdef long outer, inner, off
    cdef long cx, cy, xs, xe, ys, ye
    cdef long dx, dy, d2
    cdef unsigned char *cell
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

            for y in prange(ys, ye, use_threads_if=(ye-ys) > THRESH, nogil=True):
                if y < cTop or y > cBot:
                    continue
                dy = y - cy
                for x in range(xs, xe):
                    if x < cLeft or x > cRight:
                        continue
                    dx = x - cx
                    d2 = dx*dx + dy*dy
                    if inner <= d2 < outer:
                        cell = &arr[y, x, 0]
                        if acol == 255:
                            cell[0] = <unsigned char>(rcol)
                            cell[1] = <unsigned char>(gcol)
                            cell[2] = <unsigned char>(bcol)
                            cell[3] = 255
                        else:
                            cell[0] = <unsigned char>((racol + cell[0]*inva) >> 8)
                            cell[1] = <unsigned char>((gacol + cell[1]*inva) >> 8)
                            cell[2] = <unsigned char>((bacol + cell[2]*inva) >> 8)
                            oa = acol + cell[3]
                            if oa > 255:
                                oa = 255
                                cell[3] = <unsigned char>(oa)


cpdef drawCirc(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr,
        double[:] pos,
        double radius,
        double thickness,
        cnp.ndarray[cnp.uint8_t, ndim=1] col,
        crop):
    cdef unsigned char acol = col[3]
    if acol == 0:
        return
    cdef unsigned char inva = 255 - acol
    cdef unsigned char rcol = col[0]
    cdef unsigned long racol = col[0]*acol
    cdef unsigned char gcol = col[1]
    cdef unsigned long gacol = col[1]*acol
    cdef unsigned char bcol = col[2]
    cdef unsigned long bacol = col[2]*acol

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

    cdef long xx, yy
    cdef long dx, dy
    cdef long dist_sq
    cdef unsigned char *cell
    for yy in prange(y0, y1, use_threads_if=(y1-y0) > THRESH, nogil=True):
        dy = yy - y
        for xx in range(x0, x1):
            dx = xx - x
            dist_sq = dx*dx + dy*dy

            if innrad2 <= dist_sq <= outrad2:
                cell = &arr[yy, xx, 0]
                if acol == 255:
                    cell[0] = <unsigned char>(rcol)
                    cell[1] = <unsigned char>(gcol)
                    cell[2] = <unsigned char>(bcol)
                    cell[3] = 255
                else:
                    cell[0] = <unsigned char>((racol + cell[0]*inva) >> 8)
                    cell[1] = <unsigned char>((gacol + cell[1]*inva) >> 8)
                    cell[2] = <unsigned char>((bacol + cell[2]*inva) >> 8)
                    oa = acol + cell[3]
                    if oa > 255:
                        oa = 255
                        cell[3] = <unsigned char>(oa)


cpdef drawElipse(
        cnp.ndarray[cnp.uint8_t, ndim=3] arr,
        double[:] pos,
        double xradius,
        double yradius,
        double rotation,
        double thickness,
        cnp.ndarray[cnp.uint8_t, ndim=1] col,
        crop):
    cdef unsigned char acol = col[3]
    if acol == 0:
        return
    cdef unsigned char inva = 255 - acol
    cdef unsigned char rcol = col[0]
    cdef unsigned long racol = col[0]*acol
    cdef unsigned char gcol = col[1]
    cdef unsigned long gacol = col[1]*acol
    cdef unsigned char bcol = col[2]
    cdef unsigned long bacol = col[2]*acol

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

    cdef unsigned char *cell
    if t == 0:
        invxr = 1.0 / (xrad * xrad)
        invyr = 1.0 / (yrad * yrad)
        for yy in prange(y_min, y_max, use_threads_if=(y_max-y_min) > THRESH, nogil=True):
            dy = yy - y
            for xx in range(x_min, x_max):
                dx = xx - x

                xr = dx * cos_t + dy * sin_t
                yr = -dx * sin_t + dy * cos_t

                if xr * xr * invxr + yr * yr * invyr <= 1.0:
                    cell = &arr[yy, xx, 0]
                    if acol == 255:
                        cell[0] = <unsigned char>(rcol)
                        cell[1] = <unsigned char>(gcol)
                        cell[2] = <unsigned char>(bcol)
                        cell[3] = 255
                    else:
                        cell[0] = <unsigned char>((racol + cell[0]*inva) >> 8)
                        cell[1] = <unsigned char>((gacol + cell[1]*inva) >> 8)
                        cell[2] = <unsigned char>((bacol + cell[2]*inva) >> 8)
                        oa = acol + cell[3]
                        if oa > 255:
                            oa = 255
                            cell[3] = <unsigned char>(oa)
    else:
        inv_right = 1.0 / ((xrad + t) * (xrad + t))
        inv_bot = 1.0 / ((yrad + t) * (yrad + t))
        inv_left = 1.0 / ((xrad - t) * (xrad - t))
        inv_top = 1.0 / ((yrad - t) * (yrad - t))

        for yy in prange(y_min, y_max, use_threads_if=(y_max-y_min) > THRESH, nogil=True):
            dy = yy - y
            for xx in range(x_min, x_max):
                dx = xx - x

                xr = dx * cos_t + dy * sin_t
                yr = -dx * sin_t + dy * cos_t

                v_outer = xr * xr * inv_right + yr * yr * inv_bot
                if v_outer <= 1.0:
                    v_inner = xr * xr * inv_left + yr * yr * inv_top
                    if v_inner > 1.0:
                        cell = &arr[yy, xx, 0]
                        if acol == 255:
                            cell[0] = <unsigned char>(rcol)
                            cell[1] = <unsigned char>(gcol)
                            cell[2] = <unsigned char>(bcol)
                            cell[3] = 255
                        else:
                            cell[0] = <unsigned char>((racol + cell[0]*inva) >> 8)
                            cell[1] = <unsigned char>((gacol + cell[1]*inva) >> 8)
                            cell[2] = <unsigned char>((bacol + cell[2]*inva) >> 8)
                            oa = acol + cell[3]
                            if oa > 255:
                                oa = 255
                                cell[3] = <unsigned char>(oa)

