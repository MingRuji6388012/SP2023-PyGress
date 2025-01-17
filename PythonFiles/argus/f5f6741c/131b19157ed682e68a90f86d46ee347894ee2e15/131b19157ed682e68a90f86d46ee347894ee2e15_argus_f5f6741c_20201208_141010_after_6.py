import torch
import collections
from functools import partial
from tempfile import TemporaryFile
from typing import List, Union, Type, Set

from argus import types


class Default:
    def __repr__(self) -> str:
        return "default"


class Identity:
    def __call__(self, x: types.TVar) -> types.TVar:
        return x

    def __repr__(self) -> str:
        return "Identity()"


default = Default()
identity = Identity()


def deep_to(input, *args, **kwarg):
    if torch.is_tensor(input):
        return input.to(*args, **kwarg)
    elif isinstance(input, str):
        return input
    elif isinstance(input, collections.abc.Sequence):
        return [deep_to(sample, *args, **kwarg) for sample in input]
    elif isinstance(input, collections.abc.Mapping):
        return {k: deep_to(sample, *args, **kwarg) for k, sample in input.items()}
    elif isinstance(input, torch.nn.Module):
        return input.to(*args, **kwarg)
    else:
        return input


def deep_detach(input):
    if torch.is_tensor(input):
        return input.detach()
    elif isinstance(input, str):
        return input
    elif isinstance(input, collections.abc.Sequence):
        return [deep_detach(sample) for sample in input]
    elif isinstance(input, collections.abc.Mapping):
        return {k: deep_detach(sample) for k, sample in input.items()}
    else:
        return input


def deep_chunk(input, chunks: int, dim: int = 0):
    partial_deep_chunk = partial(deep_chunk, chunks=chunks, dim=dim)
    if torch.is_tensor(input):
        return torch.chunk(input, chunks, dim=dim)
    if isinstance(input, str):
        return [input for _ in range(chunks)]
    if isinstance(input, collections.abc.Sequence) and len(input) > 0:
        return list(map(list, zip(*map(partial_deep_chunk, input))))
    if isinstance(input, collections.abc.Mapping) and len(input) > 0:
        return list(map(type(input), zip(*map(partial_deep_chunk, input.items()))))
    else:
        return [input for _ in range(chunks)]


def device_to_str(device: types.Devices) -> Union[str, List[str]]:
    if isinstance(device, (list, tuple)):
        return [str(d) for d in device]
    else:
        return str(device)


def inheritors(cls: Type[types.TVar]) -> Set[Type[types.TVar]]:
    subclasses = set()
    cls_list = [cls]
    while cls_list:
        parent = cls_list.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                cls_list.append(child)
    return subclasses


def check_pickleble(obj):
    with TemporaryFile() as file:
        torch.save(obj, file)


def get_device_indices(devices: List[torch.device]) -> List[int]:
    device_ids = []
    for dev in devices:
        if dev.type != 'cuda':
            raise ValueError("Non CUDA device in list of devices")
        if dev.index is None:
            raise ValueError("CUDA device without index in list of devices")
        device_ids.append(dev.index)
    if len(device_ids) != len(set(device_ids)):
        raise ValueError("CUDA device indices must be unique")
    return device_ids


class AverageMeter:
    """Computes and stores the average by Welford's algorithm"""

    def __init__(self):
        self.average: float = 0
        self.count: int = 0

    def reset(self):
        self.average = 0
        self.count = 0

    def update(self, value: float, n: int = 1):
        self.count += n
        self.average += (value - self.average) / self.count
