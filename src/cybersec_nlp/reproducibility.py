"""Reproducible GPU training without affecting the rest of the session.

CUDA kernels used in training (cuBLAS reductions, atomics) are not bit-for-bit deterministic
by default, so two runs of the same notebook give slightly different fine-tuning results.
:func:`deterministic_torch` enables deterministic algorithms **only inside a block** and
restores the previous state, because other libraries used later in the same kernel (e.g. the
scatter operations of PyTorch Geometric) have no deterministic CUDA implementation.

``CUBLAS_WORKSPACE_CONFIG`` must be set before cuBLAS is first used in the process: it is set
when :mod:`cybersec_nlp.config` is imported (first cell of every notebook).
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

CUBLAS_SETTING = ":4096:8"


def configure_cublas() -> None:
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", CUBLAS_SETTING)


@contextmanager
def deterministic_torch(seed: int) -> Iterator[None]:
    import torch
    from transformers import set_seed

    previous = (torch.are_deterministic_algorithms_enabled(), torch.backends.cudnn.deterministic,
                torch.backends.cudnn.benchmark)
    set_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark = True, False
    try:
        yield
    finally:
        torch.use_deterministic_algorithms(previous[0])
        torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark = previous[1], previous[2]
