from __future__ import annotations

import os.path
import zlib

import pytest

pytest_plugins = ["mypy.test.data"]


def pytest_configure(config):
    mypy_source_root = os.path.dirname(os.path.abspath(__file__))
    if os.getcwd() != mypy_source_root:
        os.chdir(mypy_source_root)


# This function name is special to pytest.  See
# https://doc.pytest.org/en/latest/how-to/writing_plugins.html#initialization-command-line-and-configuration-hooks
def pytest_addoption(parser) -> None:
    parser.addoption(
        "--bench", action="store_true", default=False, help="Enable the benchmark test runs"
    )
    parser.addoption(
        "--shard",
        default=None,
        metavar="K/N",
        help="Run only shard K of N (1-based). Every collected test belongs to exactly one "
        "shard, chosen by a stable hash of its node id, so running shards 1..N together "
        "runs exactly the tests a run without --shard would.",
    )


def _parse_shard(value: str) -> tuple[int, int]:
    try:
        k_str, n_str = value.split("/")
        k, n = int(k_str), int(n_str)
    except ValueError:
        raise pytest.UsageError(f"--shard expects K/N, got {value!r}") from None
    if not 1 <= k <= n:
        raise pytest.UsageError(f"--shard expects 1 <= K <= N, got {value!r}")
    return k, n


def pytest_collection_modifyitems(config, items) -> None:
    value = config.getoption("--shard")
    if not value:
        return
    k, n = _parse_shard(value)
    keep = []
    drop = []
    for item in items:
        if zlib.crc32(item.nodeid.encode("utf-8")) % n == k - 1:
            keep.append(item)
        else:
            drop.append(item)
    if drop:
        config.hook.pytest_deselected(items=drop)
    items[:] = keep
