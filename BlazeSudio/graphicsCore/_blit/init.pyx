# cython: boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False
import numpy as np
cimport numpy as cnp
from BlazeSudio.speed.time cimport Timer
from cython.parallel import prange
__cimport_types__ = [cnp.ndarray]

cdef unsigned int THRESH = 300

cdef cnp.ndarray[cnp.float64_t, ndim=2] invert_affine_matrix(mat):
    cdef double a, b, tx
    cdef double c, d, ty
    a, b, tx = mat[0]
    c, d, ty = mat[1]
    cdef double det = a*d - b*c
    if det == 0:
        raise ValueError("Singular affine")
    return np.array([
        [ d/det, -b/det, (b*ty - d*tx)/det ],
        [-c/det,  a/det, (c*tx - a*ty)/det ],
        [ 0, 0, 1 ]
    ], dtype=np.float64)


cdef inline void ezblit(
        const unsigned char[:, :, ::1] src_mv,
        unsigned char[:, :, ::1] dst_mv,
        long ow, long oh,
        long cLeft, long cTop, long cRight, long cBot,
        double scalex, double scaley, long transx, long transy
        ) noexcept nogil:
    cdef long x, y, ox, oy, oa
    cdef long ylo, yhi, xlo, xhi
    cdef unsigned char sa, inva
    cdef const unsigned char *srcrow
    cdef unsigned char *dstrow
    if scalex == 1 and scaley == 1:
        ylo = max(cTop, transy)
        yhi = min(cBot, transy + oh)
        xlo = max(cLeft, transx)
        xhi = min(cRight, transx + ow)
        for y in prange(ylo, yhi, use_threads_if=(yhi-ylo) > THRESH, nogil=True):
            oy = y - transy
            for x in range(xlo, xhi):
                ox = x - transx
                srcrow = &src_mv[oy, ox, 0]
                sa = srcrow[3]
                if sa != 0:
                    dstrow = &dst_mv[y, x, 0]
                    if sa == 255:
                        dstrow[0] = srcrow[0]
                        dstrow[1] = srcrow[1]
                        dstrow[2] = srcrow[2]
                        dstrow[3] = 255
                    else:
                        inva = 255 - sa
                        dstrow[0] = <unsigned char>((srcrow[0]*sa + dstrow[0]*inva) >> 8)
                        dstrow[1] = <unsigned char>((srcrow[1]*sa + dstrow[1]*inva) >> 8)
                        dstrow[2] = <unsigned char>((srcrow[2]*sa + dstrow[2]*inva) >> 8)
                        oa = sa + dstrow[3]
                        if oa > 255:
                            oa = 255
                            dstrow[3] = <unsigned char>(oa)
        return

    cdef double dx = transx + ow * scalex
    cdef double dy = transy + oh * scaley
    xlo = max(cLeft,  <long>min(transx, dx))
    xhi = min(cRight, <long>max(transx, dx) + 1)
    ylo = max(cTop,   <long>min(transy, dy))
    yhi = min(cBot,   <long>max(transy, dy) + 1)

    cdef double inv_scalex = 1.0 / scalex
    cdef double inv_scaley = 1.0 / scaley
    for y in prange(ylo, yhi, use_threads_if=(yhi-ylo) > THRESH, nogil=True):
        oy = <long>((y - transy) * inv_scaley)
        if 0 <= oy < oh:
            for x in range(cLeft, cRight):
                ox = <long>((x - transx) * inv_scalex)
                if 0 <= ox < ow:
                    srcrow = &src_mv[oy, ox, 0]
                    sa = srcrow[3]
                    if sa != 0:
                        dstrow = &dst_mv[y, x, 0]
                        if sa == 255:
                            dstrow[0] = srcrow[0]
                            dstrow[1] = srcrow[1]
                            dstrow[2] = srcrow[2]
                            dstrow[3] = 255
                        else:
                            inva = 255 - sa
                            dstrow[0] = <unsigned char>((srcrow[0]*sa + dstrow[0]*inva) >> 8)
                            dstrow[1] = <unsigned char>((srcrow[1]*sa + dstrow[1]*inva) >> 8)
                            dstrow[2] = <unsigned char>((srcrow[2]*sa + dstrow[2]*inva) >> 8)
                            oa = sa + dstrow[3]
                            if oa > 255:
                                oa = 255
                            dstrow[3] = <unsigned char>(oa)

cdef inline void regblit(
        const unsigned char[:, :, ::1] src_mv,
        unsigned char[:, :, ::1] dst_mv,
        long ow, long oh,
        long cLeft, long cTop, long cRight, long cBot,
        bint persp, double[:, ::1] Minv
        ) noexcept nogil:
    cdef long x, y, ox, oy, oa
    cdef double oy_first, oy_last
    cdef double z = 1
    cdef double sx, sy, invz
    cdef unsigned char sa, inva
    cdef const unsigned char *srcrow
    cdef unsigned char *dstrow

    # "For efficiency" (hopefully)
    cdef double m00 = Minv[0, 0]
    cdef double m01 = Minv[0, 1]
    cdef double m02 = Minv[0, 2]
    cdef double m10 = Minv[1, 0]
    cdef double m11 = Minv[1, 1]
    cdef double m12 = Minv[1, 2]
    cdef double m20 = Minv[2, 0]
    cdef double m21 = Minv[2, 1]
    cdef double m22 = Minv[2, 2]

    for y in prange(cTop, cBot, use_threads_if=(cBot-cTop) > THRESH, nogil=True):
        oy_first = <long>(m10*cLeft + m11*y + m12)
        oy_last  = <long>(m10*(cRight-1) + m11*y + m12)
        if (oy_first < 0 and oy_last < 0) or (oy_first >= oh and oy_last >= oh):
            continue  # entire row maps outside source — skip

        sx = m00*cLeft + m01*y + m02
        sy = m10*cLeft + m11*y + m12
        if persp: z = m20*cLeft + m21*y + m22
        for x in range(cLeft, cRight):
            if z != 0:
                if persp:
                    invz = 1.0 / z
                    ox = <long>(sx * invz)
                    oy = <long>(sy * invz)
                else:
                    ox = <long>sx
                    oy = <long>sy

                if 0 <= ox < ow and 0 <= oy < oh:
                    srcrow = &src_mv[oy, ox, 0]
                    sa = srcrow[3]
                    if sa != 0:
                        dstrow = &dst_mv[y, x, 0]
                        if sa == 255:
                            dstrow[0] = srcrow[0]
                            dstrow[1] = srcrow[1]
                            dstrow[2] = srcrow[2]
                            dstrow[3] = 255
                        else:
                            inva = 255 - sa
                            dstrow[0] = <unsigned char>((srcrow[0]*sa + dstrow[0]*inva) >> 8)
                            dstrow[1] = <unsigned char>((srcrow[1]*sa + dstrow[1]*inva) >> 8)
                            dstrow[2] = <unsigned char>((srcrow[2]*sa + dstrow[2]*inva) >> 8)
                            oa = sa + dstrow[3]
                            if oa > 255:
                                oa = 255
                            dstrow[3] = <unsigned char>(oa)
            sx = sx + m00
            sy = sy + m10
            if persp: z = z + m20

def blit(
        cnp.ndarray[cnp.float64_t, ndim=2] mat,
        cnp.ndarray[cnp.uint8_t, ndim=3] src,
        cnp.ndarray[cnp.uint8_t, ndim=3] dst,
        crop):
    cdef long oh = src.shape[0]
    cdef long ow = src.shape[1]

    cdef double[:, ::1] mat_mv = mat
    cdef const unsigned char[:, :, ::1] src_mv = src
    cdef unsigned char[:, :, ::1] dst_mv = dst

    cdef long cLeft = <long>crop[0]
    cdef long cTop = <long>crop[1]
    cdef long cRight = <long>crop[2]
    cdef long cBot = <long>crop[3]

    cdef bint persp = mat_mv[2,0] != 0 or mat_mv[2,1] != 0 or mat_mv[2,2] != 1
    if (not persp) and mat_mv[0,1] == 0 and mat_mv[1,0] == 0:
        ezblit(
            src_mv, dst_mv,
            ow, oh, cLeft, cTop, cRight, cBot,
            mat_mv[0,0], mat_mv[1,1], <long>mat_mv[0,2], <long>mat_mv[1,2])
        return

    cdef cnp.ndarray[cnp.float64_t, ndim=2] Minv_
    if persp:
        Minv_ = np.linalg.inv(mat)
    else:
        Minv_ = invert_affine_matrix(mat)
    cdef double[:, ::1] Minv = Minv_

    # Instead of looping over every line in the crop space, only loop over the bounding box
    cdef double[4] dst_xs
    cdef double[4] dst_ys
    cdef double cx, cy, cz
    cdef double min_x, max_x, min_y, max_y
    cdef int i
    cdef bint bounds_valid = True

    # Source corners: (0,0), (ow,0), (0,oh), (ow,oh)
    cdef long[4] sc_x = [0, ow, 0,  ow]
    cdef long[4] sc_y = [0, 0,  oh, oh]

    for i in range(4):
        cx = mat_mv[0,0]*sc_x[i] + mat_mv[0,1]*sc_y[i] + mat_mv[0,2]
        cy = mat_mv[1,0]*sc_x[i] + mat_mv[1,1]*sc_y[i] + mat_mv[1,2]
        if persp:
            cz = mat_mv[2,0]*sc_x[i] + mat_mv[2,1]*sc_y[i] + mat_mv[2,2]
            if cz <= 0:
                # Corner behind camera — bail out, use original crop
                bounds_valid = False
                break
            cx = cx / cz
            cy = cy / cz
        dst_xs[i] = cx
        dst_ys[i] = cy

    if bounds_valid:
        min_x = max_x = dst_xs[0]
        min_y = max_y = dst_ys[0]
        for i in range(1, 4):
            if dst_xs[i] < min_x: min_x = dst_xs[i]
            if dst_xs[i] > max_x: max_x = dst_xs[i]
            if dst_ys[i] < min_y: min_y = dst_ys[i]
            if dst_ys[i] > max_y: max_y = dst_ys[i]

        cLeft  = max(cLeft,  <long>min_x)
        cTop   = max(cTop,   <long>min_y)
        cRight = min(cRight, <long>max_x + 1)
        cBot   = min(cBot,   <long>max_y + 1)

        if cLeft >= cRight or cTop >= cBot:
            return

    regblit(
        src_mv, dst_mv,
        ow, oh, cLeft, cTop, cRight, cBot,
        persp, Minv
    )

