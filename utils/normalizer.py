

import numpy as np # noqa

""" get_base_clocks:
Generates a list of base clocks based on the given start and end epochs and the unit seconds.
"""
def get_base_clocks(startep: int, endep: int, unitsecs: int) -> list[int]:
    # Adjust startep and endep to be earlier epochs that meet epoch % unitsecs == 0
    adjusted_startep = startep - (startep % unitsecs)
    adjusted_endep = endep - (endep % unitsecs)
    return list(range(adjusted_startep, adjusted_endep + unitsecs, unitsecs))


""" fit_to_base_clocks:
Adjusts the given values to fit the base clocks by interpolating or averaging the values.

This function takes three lists: base_clocks, clocks, and values. It adjusts the values to fit the base_clocks
by either directly assigning the values if the lengths match, or by interpolating/averaging the values if the lengths differ.

Args:
    base_clocks (list[int]): The list of base clock timestamps to fit the values to.
    clocks (list[int]): The list of clock timestamps corresponding to the given values.
    values (list[float]): The list of values to be adjusted to fit the base clocks.

Returns:
    list[float]: A list of values adjusted to fit the base clocks.
"""
def fit_to_base_clocks(base_clocks: list[int], clocks: list[int], values: list[float]) -> list[float]:
    if len(clocks) == len(base_clocks):
        return values
    else:
        new_values: np.ndarray = np.zeros(len(base_clocks))  
        i: int = 0
        j: int = 0
        sum_buffer: float = 0.0
        cnt_buffer: int = 0
        len_base_clocks: int = len(base_clocks)
        len_data: int = len(clocks)

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
            new_values[i:] = sum_buffer / cnt_buffer

        if i < len_base_clocks:
            new_values[i:] = [values[-1]] * (len(base_clocks) - i)

        if j < len_data:
            new_values[-1] = (new_values[-1] + np.mean(values[j:])) / 2.0

        return new_values.tolist()

