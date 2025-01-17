"""
Library to genarate test data for the project
"""
import numpy as np
import pandas as pd
import math

def gaussian_noise(num_samples, **properties):
    mean = properties.get('mean', 0)
    std = properties.get('std', 1)
    seed_val = properties.get('seed_val', 0)
    if seed_val != 0:
        np.random.seed(seed_val)
    return np.random.normal(mean, std, num_samples)

def sine_wave(num_samples, **properties):
    min_val = properties.get('min_val', 0)
    max_val = properties.get('max_val', 1)
    num_waves = properties.get('num_waves', 1)
    shift = properties.get('shift', 0)
    shift = 2.0 / num_samples * shift
    x = np.linspace(shift, 2.0 + shift, math.ceil(num_samples / num_waves), endpoint=False)
    x *= np.pi
    y = np.sin(x)
    # concat same y num_waves times
    y = np.tile(y, num_waves)

    # extend the range to min, max
    if y.size > 0:
        y = np.interp(y, (y.min(), y.max()), (min_val, max_val))

    return y

def exponential_wave(num_samples, **properties):
    min_val = properties.get('min_val', 0)
    max_val = properties.get('max_val', 1)
    num_waves = properties.get('num_waves', 1)
    shift = properties.get('shift', 0)
    shift = 2.0 / num_samples * shift
    x = np.linspace(shift, 2.0 + shift, math.ceil(num_samples / num_waves), endpoint=False)
    x *= np.pi
    y = np.exp(x)
    # extend the range to min, max
    y = np.interp(y, (y.min(), y.max()), (min_val, max_val))
    
    # concatenate the same y num_waves times
    y = np.tile(y, num_waves)

    return y

# log graph
def logarithmic_wave(num_samples, **properties):
    min_val = properties.get('min_val', 0)
    max_val = properties.get('max_val', 1)
    x = np.linspace(1, num_samples, num_samples)
    y = np.log(x)
    
    # extend the range to min, max
    y = np.interp(y, (y.min(), y.max()), (min_val, max_val))
    
    return y



# the theoretical normal distribution curve
def normal_distribution_wave(num_samples, **properties):
    min_val = properties.get('min_val', 0)
    max_val = properties.get('max_val', 1)
    mean = properties.get('mean', 0)
    std = properties.get('std', 1)
    shift = properties.get('shift', 0)
    inverse = properties.get('inverse', False)
    num_waves = properties.get('num_waves', 1)

    block_size = math.ceil(num_samples / num_waves)
    half_block_size = math.floor(block_size / 2)
    x = np.linspace(mean - half_block_size * std, mean + half_block_size * std, block_size, endpoint=False)
    y = np.exp(-0.5 * ((x - mean) / std) ** 2)

    # cut shift numbers from the beginning and add to the end
    y = np.roll(y, shift)

    if inverse:
        y = -y

    if y.size > 0:
        y = np.interp(y, (y.min(), y.max()), (min_val, max_val))
        y = np.tile(y, num_waves)
    return y
    

def tangent_wave(num_samples, **properties):
    min_val = properties.get('min_val', 0)
    max_val = properties.get('max_val', 1)
    shift = properties.get('shift', 0)
    x = np.linspace(min_val, max_val, num_samples)
    y = np.tan(x + shift)
    return y


def arctangent_wave(num_samples, **properties):
    min_val = properties.get('min_val', 0)
    max_val = properties.get('max_val', 1)
    shift = properties.get('shift', 0)
    inverse = properties.get('inverse', False)
    x = np.linspace(-1, 1, num_samples)  # Use a standard x-range for arctan
    y = np.arctan(x + shift)
    if inverse:
        y = -y
    
    # Scale y to fit within the min_val and max_val range
    y = np.interp(y, (y.min(), y.max()), (min_val, max_val))
    return y


def generate_monotonic_values(num_samples, **properties):
    start = properties.get('start', 0)
    end = properties.get('end', 1)
    return np.linspace(start, end, num_samples)

def step_function_values(num_samples, **properties):
    min_val = properties.get('min_val', 0)
    max_val = properties.get('max_val', 1)
    step_index = properties.get('step_index', num_samples // 2)
    # the first step_index are min_val, the rest are max_val
    return np.array([min_val if i < step_index else max_val for i in range(num_samples)])


# generate a stairs-like wave
def stairs_wave(num_samples, **properties):
    min_val = properties.get('min_val', 0)
    max_val = properties.get('max_val', 1)
    num_steps = properties.get('num_steps', 5)
    inverse = properties.get('inverse', False)
    noise_rate = properties.get('noise_rate', 0.0)
    seed = properties.get('seed_val', 0)
    step_size = num_samples // num_steps
    step_index = 0
    data = np.zeros(num_samples)
    for i in range(num_steps):
        step_index += step_size
        if step_index >= num_samples:
            step_index = num_samples
        step_values = step_function_values(num_samples, min_val=min_val, max_val=max_val, step_index=step_index)
        if inverse:
            step_values = max_val - step_values + min_val
        data = merge_data(data, step_values)
    
    if noise_rate > 0:
        std = (max_val-min_val)*noise_rate
        # add noise
        data += gaussian_noise(num_samples, mean=0, std=std, seed_val=seed)
    
    return data


def oneweek_normal_distribution_wave(num_samples, **properties):
    min_val = properties.get('min_val', 0)
    max_val = properties.get('max_val', 1)
    noise_rate = properties.get('noise_rate', 0.0)
    wave_shift = properties.get('wave_shift', 0)
    repeat = properties.get('repeat', 1)
    seed = properties.get('seed_val', 0)
    num_samples = num_samples // repeat
    num_weekday_samples = (num_samples // 7) * 5
    num_weekend_samples = num_samples - num_weekday_samples
    w1 = normal_distribution_wave(num_weekday_samples, num_waves=5, min_val=min_val, max_val=max_val)
    w2 = np.full(num_weekend_samples, min_val)
    data = np.concatenate((w1, w2))
    
    if repeat > 1:
        for _ in range(repeat-1):
            data = np.concatenate((data, data))


    if noise_rate > 0:
        std = (max_val-min_val)*noise_rate
        # add noise
        data += gaussian_noise(num_samples*repeat, mean=0, std=std, seed_val=seed)

    if wave_shift > 0:
        data = np.roll(data, wave_shift)
    return data


def convex_wave(num_samples, **properties):
    min_val = properties.get('min_val', 0)
    max_val = properties.get('max_val', 1)
    flat_rate = properties.get('flat_rate', 0.5)
    noise_rate = properties.get('noise_rate', 0.0)
    repeat = properties.get('repeat', 1)
    inverse = properties.get('inverse', False)
    seed = properties.get('seed_val', 0)
    num_samples = num_samples // repeat
    num_flat_samples = int(num_samples * flat_rate)
    num_convex_samples = num_samples - num_flat_samples

    const_val = min_val
    if inverse:
        const_val = max_val

    flat_part = np.full(num_flat_samples, const_val)
    convex_part = normal_distribution_wave(num_convex_samples, min_val=min_val, max_val=max_val, inverse=inverse)

    data = np.concatenate((flat_part, convex_part))

    if repeat > 1:
        for _ in range(repeat-1):
            data = np.concatenate((data, data))

    if noise_rate > 0:
        std = (max_val-min_val)*noise_rate
        # add noise
        data += gaussian_noise(num_samples*repeat, mean=0, std=std, seed=seed)

    return data
    

def merge_data(data1, data2):
    return np.add(data1, data2)

# a function to generate pandas dataframe with the given np array and timeline(epoch)
def generate_dataframe(data, start_epoch, unitsecs=300):
    end_epoch = start_epoch + len(data) * unitsecs
    timeline = list(range(start_epoch, end_epoch, unitsecs))
    df = pd.DataFrame(data, index=timeline, columns=["value"])
    return df




# function to plot the given np array
import matplotlib.pyplot as plt

def plot_wave(data, title="Waveform", xlabel="Sample", ylabel="Value"):
    plt.figure(figsize=(10, 4))
    plt.plot(data)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.show()
