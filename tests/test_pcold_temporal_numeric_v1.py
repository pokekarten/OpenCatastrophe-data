from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sys
import unittest

import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / "research-scripts" / "pcold_temporal_frequency_tournament_numeric_v1.py"
SPEC = importlib.util.spec_from_file_location("pcold_temporal_numeric_v1", SCRIPT)
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


class PCOLDTemporalNumericRepairTests(unittest.TestCase):
    def test_small_alpha_zero_counts_remain_finite(self) -> None:
        y = np.array([0.0, 0.0, 1.0, 3.0, 8.0])
        mu = np.array([0.2, 5.0, 0.8, 2.5, 6.0])
        got = m.stable_nb2_logpmf(y, mu, math.exp(-20.0))
        self.assertTrue(np.isfinite(got).all())

    def test_small_alpha_converges_numerically_to_poisson(self) -> None:
        y = np.array([0.0, 1.0, 3.0, 8.0])
        mu = np.array([0.2, 0.8, 2.5, 6.0])
        got = m.stable_nb2_logpmf(y, mu, math.exp(-20.0))
        ref = m.base.poisson_logpmf(y, mu)
        np.testing.assert_allclose(got, ref, rtol=0.0, atol=1e-6)

    def test_patch_is_installed_into_base_module(self) -> None:
        self.assertIs(m.base.nb2_logpmf, m.stable_nb2_logpmf)


if __name__ == "__main__":
    unittest.main()
