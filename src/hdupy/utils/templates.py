import functools
import inspect
from typing import Any, Literal, Protocol, cast, overload

from aiohttp import ClientResponse
from aiohttp.client import _RequestOptions as RequestOptions
from aiohttp.typedefs import StrOrURL

from .._abc import AbstractHduModule
from ..typ import AsyncCallable, P, SyncOrAsyncCallable, T, T_co
from .headers import get_headers

_TemplateMethods = Literal["GET", "POST"]
_DecoratedFuncReturns = tuple[StrOrURL, RequestOptions] | StrOrURL


class _TemplDeco(Protocol[T_co]):
    def __call__(
        self, func: SyncOrAsyncCallable[P, _DecoratedFuncReturns]
    ) -> AsyncCallable[P, T_co]: ...


def to_async(func: SyncOrAsyncCallable[P, T]) -> AsyncCallable[P, T]:
    @functools.wraps(func)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        ret = func(*args, **kwargs)
        if inspect.isawaitable(ret):
            return await ret
        return ret

    return wrapped


_HandlerT = SyncOrAsyncCallable[[ClientResponse], T]


@overload
def get_preset_result_handler(
    handle: Literal["json"],
) -> _HandlerT[Any]: ...
@overload
def get_preset_result_handler(
    handle: Literal["bytes"],
) -> _HandlerT[bytes]: ...
@overload
def get_preset_result_handler(
    handle: Literal["str"],
) -> _HandlerT[str]: ...


@functools.cache
def get_preset_result_handler(
    handle: Literal["str", "json", "bytes"],
) -> _HandlerT[Any]:
    async def handler(resp: ClientResponse):
        match handle:
            case "str":
                return await resp.text("utf-8")
            case "bytes":
                return await resp.read()
            case "json":
                return await resp.json(encoding="utf-8")

    return handler


DEFAULT_RESULT_HANDLER = get_preset_result_handler("str")


@overload
def request_template(
    result_handler: _HandlerT[T],
    method: _TemplateMethods = "GET",
) -> _TemplDeco[T]: ...
@overload
def request_template(
    result_handler: None = None,
    method: _TemplateMethods = "GET",
) -> _TemplDeco[str]: ...


def request_template(
    result_handler: _HandlerT[T] | Literal["str", "json", "bytes"] | None = None,
    method: _TemplateMethods = "GET",
) -> _TemplDeco[T | Any]:
    """Can be applied to method of child class of AbstractHduModule"""
    if result_handler is None:
        _ = DEFAULT_RESULT_HANDLER
    elif isinstance(result_handler, str):
        _ = get_preset_result_handler(result_handler)
    else:
        _ = result_handler
    handler = to_async(_)

    def decorator(
        func: SyncOrAsyncCallable[P, _DecoratedFuncReturns],
    ) -> AsyncCallable[P, Any]:
        @functools.wraps(func)
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> Any:
            self = cast(AbstractHduModule, args[0])
            params: RequestOptions = {}
            _ = await to_async(func)(*args, **kwargs)
            if isinstance(_, tuple):
                url, params = _
            else:
                url = _
            params["headers"] = get_headers(updates=params.get("headers"))
            async with self.session.request(method=method, url=url, **params) as resp:
                return await handler(resp)

        return wrapped

    return decorator
