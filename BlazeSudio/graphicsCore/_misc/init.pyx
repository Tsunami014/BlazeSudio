# cython: boundscheck=False, wraparound=False, nonecheck=False, cdivision=True, initializedcheck=False
import numpy as np
cimport numpy as cnp
from libc.stdint cimport uint32_t, uint64_t
from cython.parallel import prange
__cimport_types__ = [cnp.ndarray]

cdef unsigned int THRESH = 512


cdef inline void blend_innr(unsigned char* pixel,
         uint32_t racol, uint32_t gacol, uint32_t bacol,
         unsigned char acol, unsigned char inva) noexcept nogil:
    pixel[0] = <unsigned char>((racol + pixel[0]*inva) >> 8)
    pixel[1] = <unsigned char>((gacol + pixel[1]*inva) >> 8)
    pixel[2] = <unsigned char>((bacol + pixel[2]*inva) >> 8)
    pixel[3] = <unsigned char>(acol + ((pixel[3]*inva) >> 8))

cdef void fill_trans(unsigned char[:, :, ::1] arr,
                unsigned char[::1] col) noexcept nogil:
    cdef unsigned char acol = col[3]
    if acol == 0:
        return
    cdef unsigned char inva = 256 - acol
    cdef uint32_t racol = col[0]*acol
    cdef uint32_t gacol = col[1]*acol
    cdef uint32_t bacol = col[2]*acol
    cdef uint32_t *p32 = <uint32_t*> (&arr[0,0,0])
    cdef long n = arr.shape[0] * arr.shape[1]
    cdef long i
    for i in prange(n, nogil=True, schedule='static', use_threads_if=n > THRESH):
        blend_innr(<unsigned char*>(&p32[i]), racol, gacol, bacol, acol, inva)

cpdef fill_arr(cnp.ndarray[cnp.uint8_t, ndim=3] arr,
               cnp.ndarray[cnp.uint8_t, ndim=1] col):
    if col[3] < 255:
        fill_trans(arr, col)
        return
    cdef unsigned char rcol = col[0]
    cdef unsigned char gcol = col[1]
    cdef unsigned char bcol = col[2]
    cdef long n = arr.shape[0] * arr.shape[1]
    cdef uint32_t c32 = (rcol) | (gcol << 8) | (bcol << 16) | (255 << 24)
    cdef uint32_t *p32 = <uint32_t*> (&arr[0,0,0])

    cdef uint64_t c64 = (<uint64_t>c32 << 32) | <uint64_t>c32
    cdef uint64_t* p64 = <uint64_t*>p32
    cdef long n2 = n >> 1

    cdef long i
    for i in prange(n2, nogil=True, schedule='static', use_threads_if=n2 > THRESH):
        p64[i] = c64
    if n & 1:
        p32[n-1] = c32
