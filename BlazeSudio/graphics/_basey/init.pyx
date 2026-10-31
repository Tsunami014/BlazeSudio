# cython: boundscheck=False, wraparound=False, nonecheck=False, cdivision=True, initializedcheck=False
import numpy as np
cimport numpy as cnp
__cimport_types__ = [cnp.ndarray]

cdef class Base:
    def _warpPs(self, mat: np.ndarray, points: np.ndarray):
        points = points.astype(float)
        if self._affMat(mat):
            return points @ mat[:2, :2].T + mat[:2, 2]
        p = np.c_[points, np.ones(len(points))] @ mat.T
        return p[:, :2] / p[:, 2:3]

    cpdef bint _regMat(self,
            cnp.ndarray[cnp.float64_t, ndim=2] mat):
        """Returns True if a matrix is 'regular' - no rotations or perspective warps"""
        cdef double[:, ::1] mat_mv = mat
        return (
            mat_mv[2, 0] == 0 and mat_mv[2, 1] == 0 and mat_mv[2, 2] == 1 and
            (
                (mat_mv[0,1] == 0 and mat_mv[1,0] == 0) or
                (mat_mv[0,0] == 0 and mat_mv[1,1] == 0)
            )
        )
    cpdef bint _affMat(self,
            cnp.ndarray[cnp.float64_t, ndim=2] mat):
        """Returns True if a matrix is 'affine' - no perspective warps"""
        cdef double[:, ::1] mat_mv = mat
        return mat_mv[2, 0] == 0 and mat_mv[2, 1] == 0 and mat_mv[2, 2] == 1

    cpdef cnp.ndarray[cnp.float64_t, ndim=2] _regWarp(self,
            cnp.ndarray[cnp.float64_t, ndim=2] mat, object p, bint offset = True):
        """Warps a point assuming no perspective warp (bottom row is [0, 0, 1])"""
        cdef double[:, ::1] mat_mv = mat
        cdef double x = p[0]
        cdef double y = p[1]
        if offset:
            return np.array([
                x*mat_mv[0, 0] + y*mat_mv[0, 1] + mat_mv[0, 2],
                x*mat_mv[1, 0] + y*mat_mv[1, 1] + mat_mv[1, 2]
            ], dtype=float)
        else:
            return np.array([
                x*mat_mv[0, 0] + y*mat_mv[0, 1],
                x*mat_mv[1, 0] + y*mat_mv[1, 1]
            ], dtype=float)

    cpdef object _warpbbx(self,
            cnp.ndarray[cnp.float64_t, ndim=2] mat, object crop, object outercrop):
        topL = crop[:2]
        botR = crop[2:]
        if self._regMat(mat):
            ps = [
                self._regWarp(mat, topL),
                self._regWarp(mat, botR)
            ]
        else:
            ps = self._warpPs(mat, np.array([
                topL,
                [topL[0], botR[1]],
                botR,
                [botR[0], topL[1]]
            ], float))
        cdef left = ps[0][0]
        cdef top = ps[0][1]
        cdef right = ps[0][0]
        cdef bot = ps[0][1]
        for p in ps[1:]:
            if p[0] < left:
                left = p[0]
            if p[0] > right:
                right = p[0]
            if p[1] < top:
                top = p[1]
            if p[1] > bot:
                bot = p[1]
        if outercrop[2] != 0:
            if outercrop[0] > left:
                left = outercrop[0]
            if outercrop[2] < right:
                right = outercrop[2]
            if outercrop[1] > top:
                top = outercrop[1]
            if outercrop[3] < bot:
                bot = outercrop[3]
        if left >= right or top >= bot:
            return (0,0,0,0)
        return (left, top, right, bot)

