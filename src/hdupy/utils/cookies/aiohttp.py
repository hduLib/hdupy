from collections.abc import Iterable
from http.cookies import Morsel
from typing import TypedDict

from aiohttp.cookiejar import CookieJar


class CookieDict(TypedDict):
    key: str
    value: str
    metadata: dict[str, str]


def cookiejar_to_dicts(cj: CookieJar):
    """cj 能从 ClientSession 的 cookiejar 属性拿到"""
    result: list[CookieDict] = []
    for cookie in cj:
        result.append(
            {"key": cookie.key, "value": cookie.value, "metadata": dict(cookie)}
        )
    return result


def dicts_to_loosecookies(cookies: Iterable[CookieDict]):
    """返回值能够被传递给 ClientSession 的 cookies 参数"""
    result: dict[str, Morsel[str]] = {}
    for cookie in cookies:
        ms = Morsel[str]()
        ms.set(cookie["key"], cookie["value"], cookie["value"])
        ms.update(cookie["metadata"])
        result[ms.key] = ms
    return result
