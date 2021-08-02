from importlib import reload
import importlib
import inspect
import os
from collections import defaultdict

import numpy as np
import lmfit
from lmfit import minimize, Parameters

from qcrew.analyze.fit_funcs import *

FIT_FUNCS = {}

# for name in os.listdir(os.path.dirname(fit_funcs.__file__)):
#     if name == "__init__.py" or not name.endswith(".py"):
#         continue
#     name = name[:-3]
#     mod = importlib.import_module("qcrew.codebase.analysis.fit_funcs." + name)
#     reload(mod)
#     func = getattr(mod, "func")
#     guess = getattr(mod, "guess")
#     FIT_FUNCS[name] = func, guess
# del name, mod, func, guess


def eval_fit(fit_func, params, xs, ys=None):
    if isinstance(fit_func, str):
        fit_func = FIT_FUNCS[fit_func][0]
    func_args = inspect.getargspec(fit_func)[0]
    kwargs = {k: p.value for k, p in params.items()}
    kwargs["params"] = params
    kwargs["xs"] = xs
    kwargs["ys"] = ys
    return fit_func(**{k: v for k, v in kwargs.items() if k in func_args})


def params_from_guess(guess):
    params = Parameters()
    for name, data in guess.items():
        if isinstance(data, tuple):
            init, min, max = data
            if min == max:
                params.add(name, init, vary=False)
            else:
                params.add(name, init, min=min, max=max)
        else:
            params.add(name, data)
    return params


def get_guess(fit_func, xs, ys, zs=None):
    guess_fn = FIT_FUNCS[fit_func][1]
    if zs is None:
        guess_args = dict(xs=xs, ys=ys)
    else:
        guess_args = dict(xs=xs, ys=ys, zs=zs)
    return params_from_guess(guess_fn(**guess_args))


def do_fit(
    fit_func, xs, ys, zs=None, guess_func=None, init_params=None, fixed_params=None
):
    if isinstance(fit_func, str):
        fit_func, _guess = FIT_FUNCS[fit_func]
        if guess_func is None:
            guess_func = _guess
    if zs is None:
        assert xs.ndim == 1
        assert ys.ndim == 1
        eval_args = dict(xs=xs)
        guess_args = dict(xs=xs, ys=ys)
        data = ys
    else:
        assert xs.ndim == 2
        assert ys.ndim == 2
        assert zs.ndim == 2
        eval_args = dict(xs=xs, ys=ys)
        guess_args = dict(xs=xs, ys=ys, zs=zs)
        data = zs
    if init_params is None and guess_func is None:
        raise ValueError(
            "If not using builtin fit function, must "
            "supply either a guess_func or init_params"
        )
    if init_params is None:
        init_params = params_from_guess(guess_func(**guess_args))

    if fixed_params is not None:
        for k, v in fixed_params.items():
            init_params[k].value = v
            init_params[k].vary = False

    def resids(params):
        return data.flatten() - eval_fit(fit_func, params, **eval_args).flatten()

    result = minimize(resids, init_params)
    if lmfit.__version__ >= "0.9.0":
        return result.params
    else:
        return init_params


def map_fit(results, dsname, fit_func, thresh=True, mean=True, fit_axis=0):
    ds = results[dsname]
    if thresh:
        ds = ds.threshold()
    if mean:
        ds = ds.axis_mean()
    xs = ds.ax_data[fit_axis]
    data = defaultdict(list)
    errs = defaultdict(list)
    rs_data = np.rollaxis(ds.data, fit_axis)
    new_shape = rs_data.shape[1:]
    rs_data = rs_data.reshape((rs_data.shape[0], -1))
    for slice in rs_data.T:
        params = do_fit(fit_func, xs, slice)
        for k, v in params.items():
            data[k].append(v.value)
            errs[k].append(v.stderr)
    new_ax_data = ds.ax_data[:]
    new_ax_data.pop(fit_axis)
    new_labels = ds.labels[:]
    new_labels.pop(fit_axis)
    for k, v in data.items():
        results[dsname + ":" + k] = np.array(v).reshape(new_shape)
        results[dsname + ":" + k].ax_data = new_ax_data
        results[dsname + ":" + k].labels = new_labels
        results[dsname + ":" + k].err_data = np.array(errs[k]).reshape(new_shape)
