"""Modified version of memory_profiler.profile that also returns the memory usage per line."""

from dataclasses import dataclass
from functools import partial, wraps
from typing import IO, Callable, Literal, Optional, ParamSpec, TypeVar, cast, overload

from memory_profiler import LineProfiler, choose_backend

try:
    import tracemalloc

    HAS_TRACEMALLOC = True
except ImportError:
    HAS_TRACEMALLOC = False

P = ParamSpec("P")  # pylint: disable=invalid-name
R = TypeVar("R")

BackendOptions = Literal["psutil", "psutil_pss", "psutil_uss", "posix", "tracemalloc"]

LineNo = int
MemInc = float
MemTot = float
MemOcc = int
MemMeasure = tuple[MemInc, MemTot, MemOcc]


@dataclass
class ProfilerRecord:
    """Dataclass for storing the profiling result for a single line."""

    line: LineNo
    increment: MemInc
    total: MemTot
    occurrences: MemOcc


ProfilerResult = list[ProfilerRecord]
ProfiledCallable = Callable[P, tuple[R, ProfilerResult]]


@overload
def profile(
    func: Callable[P, R],
    stream: Optional[IO[str]] = None,
    precision: int = 1,
    backend: BackendOptions = "psutil",
) -> ProfiledCallable[P, R]:
    ...


@overload
def profile(
    func: None = None,
    stream: Optional[IO[str]] = None,
    precision: int = 1,
    backend: BackendOptions = "psutil",
) -> Callable[[Callable[P, R]], ProfiledCallable[P, R]]:
    ...


def profile(
    func: Optional[Callable[P, R]] = None,
    stream: Optional[IO[str]] = None,
    precision: int = 1,
    backend: BackendOptions = "psutil",
) -> ProfiledCallable[P, R] | Callable[[Callable[P, R]], ProfiledCallable[P, R]]:
    """Decorator that will run the function and print a line-by-line profile"""
    backend = cast(BackendOptions, choose_backend(backend))
    if backend == "tracemalloc" and HAS_TRACEMALLOC and not tracemalloc.is_tracing():
        tracemalloc.start()

    if func is not None:
        get_prof = partial(LineProfiler, backend=backend)

        @wraps(wrapped=func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> tuple[R, ProfilerResult]:
            prof = get_prof()
            val = cast(R, prof(func)(*args, **kwargs))

            res: ProfilerResult = [
                ProfilerRecord(lineno, *mem)
                for _, lines in prof.code_map.items()
                for lineno, mem in lines
                if mem
            ]
            return val, res

        return wrapper

    # func is None
    def inner_wrapper(func: Callable[P, R]) -> ProfiledCallable[P, R]:
        return profile(func, stream=stream, precision=precision, backend=backend)

    return inner_wrapper
