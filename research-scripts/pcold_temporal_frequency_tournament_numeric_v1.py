#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sys

import numpy as np
from scipy.special import gammaln

BASE = Path(__file__).with_name("pcold_temporal_frequency_tournament.py")
SPEC = importlib.util.spec_from_file_location("pcold_temporal_frequency_tournament_base", BASE)
assert SPEC and SPEC.loader
base = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = base
SPEC.loader.exec_module(base)


def stable_nb2_logpmf(y: np.ndarray, mu: np.ndarray, alpha: float) -> np.ndarray:
    """Exact NB2 log-PMF using a stable algebraic form near the Poisson boundary."""
    if alpha <= 1e-10:
        return base.poisson_logpmf(y, mu)
    y = np.asarray(y, dtype=float)
    mu = np.clip(np.asarray(mu, dtype=float), 1e-12, 1e12)
    r = 1.0 / alpha
    return (
        gammaln(y + r)
        - gammaln(r)
        - gammaln(y + 1.0)
        - r * np.log1p(mu / r)
        + y * (np.log(mu) - np.log(r + mu))
    )


# Numerical-only amendment: every existing model/score path resolves this global
# function from the base module at call time. No model, optimizer, domain, seed,
# source rule, split or threshold changes.
base.nb2_logpmf = stable_nb2_logpmf


def main() -> None:
    base.main()


if __name__ == "__main__":
    main()
