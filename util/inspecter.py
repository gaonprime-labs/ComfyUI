import torch
from util.logger import lg
import json
import pprint


def _inspect(d):
    if isinstance(d, dict):
        out = {}
        for k in d:
            out[k] = _inspect(d[k])
    elif isinstance(d, list):
        out = [_inspect(x) for x in d]
    elif isinstance(d, tuple):
        out = tuple([_inspect(x) for x in d])
    elif isinstance(d, torch.Tensor):
        out = f"torch.Tensor({d.dtype}, {d.shape})"
    else:
        out = d
    return out


def inspect(name, d):
    lg.debug(f"{name}: {pprint.pformat(_inspect(d), indent=1, width=120)}")
