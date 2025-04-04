from collections.abc import Awaitable
from typing import ParamSpec, Protocol, TypeVar

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
P = ParamSpec("P")


class AsyncCallable(Protocol[P, T_co]):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Awaitable[T_co]: ...


class SyncOrAsyncCallable(Protocol[P, T_co]):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T_co | Awaitable[T_co]: ...
