# cython: language_level=3
# distutils: language = c++

import numpy as np
cimport numpy as np
from libc.math cimport sqrt

np.import_array()


def fast_moving_average(np.ndarray[np.float64_t, ndim=1] closes, int period):
    cdef int n = closes.shape[0]
    cdef int i, j
    cdef double s
    cdef np.ndarray[np.float64_t, ndim=1] result = np.empty(n, dtype=np.float64)

    for i in range(n):
        if i < period - 1:
            result[i] = np.nan
        else:
            s = 0.0
            for j in range(i - period + 1, i + 1):
                s += closes[j]
            result[i] = s / period

    return result


def fast_rsi(np.ndarray[np.float64_t, ndim=1] closes, int period=14):
    cdef int n = closes.shape[0]
    if n < period + 1:
        return 50.0

    cdef double avg_gain = 0.0
    cdef double avg_loss = 0.0
    cdef double delta
    cdef int i

    for i in range(1, period + 1):
        delta = closes[i] - closes[i - 1]
        if delta > 0:
            avg_gain += delta
        else:
            avg_loss += (-delta)

    avg_gain /= period
    avg_loss /= period

    if avg_loss == 0:
        return 100.0

    cdef double rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def fast_std(np.ndarray[np.float64_t, ndim=1] values):
    cdef int n = values.shape[0]
    if n < 2:
        return 0.0

    cdef double mean = 0.0
    cdef double variance = 0.0
    cdef int i

    for i in range(n):
        mean += values[i]
    mean /= n

    for i in range(n):
        variance += (values[i] - mean) * (values[i] - mean)
    variance /= (n - 1)

    return sqrt(variance)
