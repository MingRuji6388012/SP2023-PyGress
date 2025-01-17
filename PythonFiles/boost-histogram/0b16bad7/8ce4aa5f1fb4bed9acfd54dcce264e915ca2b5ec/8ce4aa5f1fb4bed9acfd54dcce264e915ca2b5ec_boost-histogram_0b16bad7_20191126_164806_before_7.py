from __future__ import absolute_import, division, print_function

del absolute_import, division, print_function

__all__ = (
    "Storage",
    "Int",
    "Double",
    "AtomicInt",
    "Unlimited",
    "Weight",
    "Mean",
    "WeightedMean",
)


from ._internal.storage import (
    Storage,
    Int,
    Double,
    AtomicInt,
    Unlimited,
    Weight,
    Mean,
    WeightedMean,
)

from ._internal.utils import register as _register

# Warnings to be removed after 0.6


int = Int()
int._warning = "int"

double = Double()
double._warning = "double"

unlimited = Unlimited()
unlimited._warning = "unlimited"

atomic_int = AtomicInt()
atomic_int._warning = "atomic_int"

weight = Weight()
weight._warning = "weight"

mean = Mean()
mean._warning = "mean"

weighted_mean = WeightedMean()
weighted_mean._warning = "weighted_mean"

del _register
