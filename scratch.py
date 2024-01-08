#%% # ==================================================== #
#
# ======================================================== #
# import module
# from module import *
# # from module import g

# f()
# module.g()

#%% # ==================================================== #
#
# ======================================================== #
import heapq

q = []

heapq.heappush(q, (2, 'code'))
heapq.heappush(q, (3, 'code'))
heapq.heappush(q, (4, 'code'))
print(heapq.heappop(q))

#%% # ==================================================== #
#
# ======================================================== #
import torch
import numpy as np
from PIL import Image
import pathlib

str(pathlib.Path("/a/b/c.txt").parent)

torch.from_numpy(
    np.array(Image.open("/home/hosan/workspace/primelabs/services/ComfyUI/output/ComfyUI_00001_.png")))

#%% # ==================================================== #
#
# ======================================================== #
from util.all import *

file_suffix("dssfd.x")

#%% # ==================================================== #
#
# ======================================================== #
import traceback
try:
    assert False
except Exception as e:
    print("stack", traceback.format_exc())
    print("e", e)
