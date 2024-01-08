import numpy as np
import nodes
import comfy
import comfy.samplers
import torch
from util.all import *


def mrange(*iterables):
    if not iterables:
        yield []
    else:
        for item in iterables[0]:
            for rest_tuple in mrange(*iterables[1:]):
                yield [item] + rest_tuple


class CustomIntList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "key": ("STRING", {
                    "default": "key"
                }),
                "start": ("INT", {
                    "default": 0,
                    "min": np.iinfo(np.int32).min,
                    "max": np.iinfo(np.int32).max,
                }),
                "end": ("INT", {
                    "default": 1,
                    "min": np.iinfo(np.int32).min,
                    "max": np.iinfo(np.int32).max,
                }),
                "inc": ("INT", {
                    "default": 1,
                    "min": np.iinfo(np.int32).min,
                    "max": np.iinfo(np.int32).max,
                }),
            }
        }

    RETURN_TYPES = ("CONFIG", )
    FUNCTION = "run"
    CATEGORY = "custom"
    OUTPUT_IS_LIST = [True]

    def run(self, key, start, end, inc):
        return ([{key: int(e)} for e in range(start, end, inc)], )


class CustomFloatList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "key": ("STRING", {
                    "default": "key"
                }),
                "start": ("FLOAT", {
                    "default": 0.0
                }),
                "end": ("FLOAT", {
                    "default": 1.0
                }),
                "inc": ("FLOAT", {
                    "default": 1.0
                }),
            }
        }

    RETURN_TYPES = ("CONFIG", )
    FUNCTION = "run"
    CATEGORY = "custom"
    OUTPUT_IS_LIST = [True]

    def run(self, key, start, end, inc):
        return ([{key: float(e)} for e in np.arange(start, end, inc)], )


class CustomStringListBySplit:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "strings": ("STRING", {
                    "default": ""
                }),
                "delimiter": ("STRING", {
                    "default": ","
                }),
                "keyout": ("STRING", {
                    "default": "path"
                }),
            }
        }

    RETURN_TYPES = ("CONFIG", )
    FUNCTION = "run"
    CATEGORY = "custom"
    OUTPUT_IS_LIST = [True]

    def run(self, strings, delimiter, keyout):
        with lg.context("CustomStringListBySplit"):
            inspect("run.input", {
                "strings": strings,
                "delimiter": delimiter,
                "keyout": keyout,
            })
            out = [{keyout: e} for e in strings.split(delimiter)]
            inspect("run.out", out)
            return (out, )


class CustomCombinator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mode": (["multiply", "simple"], {
                    "default": "multiply",
                }),
                "value1": ("CONFIG", ),
            },
            "optional": {
                "value2": ("CONFIG", ),
                "value3": ("CONFIG", ),
                "value4": ("CONFIG", ),
                "value5": ("CONFIG", ),
                "value6": ("CONFIG", ),
                "value7": ("CONFIG", ),
                "value8": ("CONFIG", ),
                "value9": ("CONFIG", ),
                "value10": ("CONFIG", ),
            }
        }

    RETURN_TYPES = ("CONFIG", )
    FUNCTION = "run"
    CATEGORY = "custom"
    INPUT_IS_LIST = [True, True, True, True, True, True, True, True, True, True]
    OUTPUT_IS_LIST = [True]

    def run(self, mode, value1, value2=None, value3=None, value4=None, value5=None, value6=None, value7=None,
            value8=None, value9=None, value10=None):
        with lg.context("CustomCombinator10"):
            values = list(
                filter(lambda e: e is not None,
                       [value1, value2, value3, value4, value5, value6, value7, value8, value9, value10]))
            inspect("run.input", {"mode": mode, "values": values})
            if not (len(values) > 0):
                raise Exception(
                    f"CustomCombinator10: assert fail: len(values) > 0: len(values)={len(values)}")

            if "multiply" in mode:
                items = list(mrange(*values))  # [x,y], [a,b,c], [p,q]] => [{**x,**a,**p}, ...]
                outs = []
                for item in items:
                    out = {}
                    for d in item:
                        out.update(d)
                    outs.append(out)
                return (outs, )
            elif "simple" in mode:
                for value in values:
                    if not (len(value) == len(values[0])):
                        raise Exception(
                            f"CustomCombinator10: assert fail: len(value) == len(values[0]): len(value)={len(value)}, len(values[0])={len(values[0])}"
                        )
                outs = []
                for item in zip(*values):
                    out = {}
                    for d in item:
                        out.update(d)
                    outs.append(out)
                return (outs, )
            else:
                raise Exception(f"CustomCombinator10: not supported mode {mode}")


NODE_CLASS_MAPPINGS = {
    "CustomIntList": CustomIntList,
    "CustomFloatList": CustomFloatList,
    "CustomStringListBySplit": CustomStringListBySplit,
    "CustomCombinator": CustomCombinator,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CustomIntList": "CustomIntList Node",
    "CustomFloatList": "CustomFloatList Node",
    "CustomStringListBySplit": "CustomStringListBySplit Node",
    "CustomCombinator": "CustomCombinator Node",
}
