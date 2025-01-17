import numpy as np
from libc.math cimport floor

cdef list fit_to_base_clocks(list base_clocks, list clocks, list values):
    """
    Adjusts the given values to fit the base clocks by interpolating or averaging the values.

    Args:
        base_clocks (list[int]): The list of base clock timestamps to fit the values to.
        clocks (list[int]): The list of clock timestamps corresponding to the given values.
        values (list[float]): The list of values to be adjusted to fit the base clocks.

    Returns:
        list[float]: A list of values adjusted to fit the base clocks.
    """
    cdef int len_base_clocks = len(base_clocks)
    cdef int len_data = len(clocks)
    cdef int i = 0, j = 0
    cdef double sum_buffer = 0.0
    cdef int cnt_buffer = 0

    if len_data == len_base_clocks:
        return values

    new_values = [0.0] * len_base_clocks

    while i < len_base_clocks and j < len_data:
        if clocks[j] > base_clocks[i]:
            new_values[i] = values[j]
            i += 1
        elif clocks[j] == base_clocks[i]:
            if cnt_buffer == 0:
                new_values[i] = values[j]
            else:
                sum_buffer += values[j]
                cnt_buffer += 1
                new_values[i] = sum_buffer / cnt_buffer
                sum_buffer = 0
                cnt_buffer = 0
            i += 1
            j += 1
        else:
            sum_buffer += values[j]
            cnt_buffer += 1
            j += 1

    if cnt_buffer > 0:
        for k in range(i, len_base_clocks):
            new_values[k] = sum_buffer / cnt_buffer

    if i < len_base_clocks:
        for k in range(i, len_base_clocks):
            new_values[k] = values[-1]

    if j < len_data:
        mean_remainder = np.mean(values[j:])
        new_values[-1] = (new_values[-1] + mean_remainder) / 2.0

    return new_values
