import numpy as np
import pandas as pd
import inspect
from numba import jit, vectorize, guvectorize
from functools import wraps


def extract_array(f):
    """
    A sanity check decorator. When combined with numba.vectorize
    or guvectorize, it provides the same capability as dataframe_vectorize
    or dataframe_guvectorize
    """
    def wrapper(*args, **kwargs):
        arrays = [arg.values for arg in args]
        return f(*arrays)
    return wrapper


def dataframe_guvectorize(dtype_args, dtype_sig):
    """
    Extracts numpy arrays from caller arguments and passes them
    to guvectorized numba functions
    """
    def make_wrapper(func):
        vecd_f = guvectorize(dtype_args, dtype_sig)(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # np_arrays = [getattr(args[0], i).values for i in theargs]
            arrays = [arg.values for arg in args]
            ans = vecd_f(*arrays)
            return ans
        return wrapper
    return make_wrapper


def dataframe_vectorize(dtype_args):
    """
    Extracts numpy arrays from caller arguments and passes them
    to vectorized numba functions
    """
    def make_wrapper(func):
        vecd_f = vectorize(dtype_args)(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # np_arrays = [getattr(args[0], i).values for i in theargs]
            arrays = [arg.values for arg in args]
            ans = vecd_f(*arrays)
            return ans
        return wrapper
    return make_wrapper


def dataframe_wrap_guvectorize(dtype_args, dtype_sig):
    """
    Extracts particular numpy arrays from caller argments and passes
    them to guvectorize. Goes one step further than dataframe_guvectorize
    by looking for the column names in the dataframe and just extracting those
    """
    def make_wrapper(func):
        theargs = inspect.getargspec(func).args
        vecd_f = guvectorize(dtype_args, dtype_sig)(func)

        def wrapper(*args, **kwargs):
            np_arrays = [getattr(args[0], i).values for i in theargs]
            ans = vecd_f(*np_arrays)
            return ans
        return wrapper
    return make_wrapper


def expand_1D(x, inflation_rate=0.02, num_years=10):
    """
    Expand the given data to account for the given number of budget years.
    If necessary, pad out additional years by increasing the last given
    year at the provided inflation rate.
    """
    if isinstance(x, np.ndarray):
        if len(x) >= num_years:
            return x
        else:
            ans = np.zeros(num_years)
            ans[:len(x)] = x
            extra = [float(x[-1])*pow(1. + inflation_rate, i) for i in
                     range(1, num_years - len(x) + 1)]
            ans[len(x):] = extra
            return ans.astype(x.dtype, casting='unsafe')

    return expand_1D(np.array([x]))


def expand_2D(x, inflation_rate=0.02, num_years=10):
    """
    Expand the given data to account for the given number of budget years.
    For 2D arrays, we expand out the number of rows until we have num_years
    number of rows. For each expanded row, we inflate by the given inflation
    rate.
    """

    if isinstance(x, np.ndarray):
        if x.shape[0] >= num_years:
            return x
        else:
            ans = np.zeros((num_years, x.shape[1]))
            ans[:len(x), :] = x
            extra = [x[-1, :]*pow(1. + inflation_rate, i) for i in
                     range(1, num_years - len(x) + 1)]
            ans[len(x):, :] = extra
            return ans.astype(x.dtype, casting='unsafe')

    return expand_2D(np.array([x]))


def expand_array(x, inflation_rate=0.02, num_years=10):
    """
    Dispatch to either expand_1D or expand2D depending on the dimension of x
    """
    try:
        if len(x.shape) == 1:
            return expand_1D(x)
        elif len(x.shape) == 2:
            return expand_2D(x)
        else:
            raise ValueError("Need a 1D or 2D array")
    except AttributeError as ae:
        raise ValueError("Must pass a numpy array")
