"""Modified version of memory_profiler.profile that also returns the memory usage per line."""

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

LineNo = int
MemInc = float
MemTot = float
MemOcc = float
MemMeasure = tuple[MemInc, MemTot, MemOcc]


@overload
def profile(
    func: Callable[P, R],
    stream: Optional[IO[str]] = None,
    precision: int = 1,
    backend: Literal[
        "psutil", "psutil_pss", "psutil_uss", "posix", "tracemalloc"
    ] = "psutil",
) -> Callable[P, tuple[R, list[tuple[LineNo, MemMeasure]]]]:
    ...


@overload
def profile(
    func: None = None,
    stream: Optional[IO[str]] = None,
    precision: int = 1,
    backend: Literal[
        "psutil", "psutil_pss", "psutil_uss", "posix", "tracemalloc"
    ] = "psutil",
) -> Callable[[Callable[P, R]], Callable[P, tuple[R, list[tuple[LineNo, MemMeasure]]]]]:
    ...


def profile(
    func: Optional[Callable[P, R]] = None,
    stream: Optional[IO[str]] = None,
    precision: int = 1,
    backend: Literal[
        "psutil", "psutil_pss", "psutil_uss", "posix", "tracemalloc"
    ] = "psutil",
) -> (
    Callable[P, tuple[R, list[tuple[LineNo, MemMeasure]]]]
    | Callable[[Callable[P, R]], Callable[P, tuple[R, list[tuple[LineNo, MemMeasure]]]]]
):
    """
    Decorator that will run the function and print a line-by-line profile
    """
    backend = cast(
        Literal["psutil", "psutil_pss", "psutil_uss", "posix", "tracemalloc"],
        choose_backend(backend),
    )
    if backend == "tracemalloc" and HAS_TRACEMALLOC:
        if not tracemalloc.is_tracing():
            tracemalloc.start()

    if func is not None:
        get_prof = partial(LineProfiler, backend=backend)

        @wraps(wrapped=func)
        def wrapper(
            *args: P.args, **kwargs: P.kwargs
        ) -> tuple[R, list[tuple[LineNo, MemMeasure]]]:
            prof = get_prof()
            val = cast(R, prof(func)(*args, **kwargs))

            res: list[tuple[LineNo, MemMeasure]] = [
                (lineno, mem)
                for _, lines in prof.code_map.items()
                for lineno, mem in lines
                if mem
            ]
            return val, res

        return wrapper

    def inner_wrapper(
        func: Callable[P, R]
    ) -> Callable[P, tuple[R, list[tuple[LineNo, MemMeasure]]]]:
        return profile(func, stream=stream, precision=precision, backend=backend)

    return inner_wrapper
