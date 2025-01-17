import unittest

import numpy as np

from audiomate.processing import pipeline


class MeanVarianceNormTest(unittest.TestCase):
    def test_compute(self):
        frame = np.random.random_sample(5)
        mean = float(np.mean(frame))
        var = float(np.var(frame))

        norm = pipeline.MeanVarianceNorm(mean, var)
        output = norm.process(frame, 4)
        expected = (frame - mean) / np.std(frame)

        assert np.array_equal(output, expected)
