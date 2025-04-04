from collections.abc import Iterable
from http.cookiejar import Cookie, CookieJar
from typing import TypedDict, cast


class CookieDict(TypedDict):
    name: str
    value: str | None
    version: int | None
    port: str | None
    port_specified: bool
    domain: str
    domain_specified: bool
    domain_initial_dot: bool
    path: str
    path_specified: bool
    secure: bool
    expires: int | None
    discard: bool
    comment: str | None
    comment_url: str | None
    rest: dict[str, str]
    rfc2109: bool


def cookiejar_to_dicts(cj: CookieJar):
    return [cookie_to_dict(c) for c in cj]


def cookie_to_dict(c: Cookie):
    result = c.__dict__.copy()
    result["rest"] = result.pop("_rest", {})
    return cast(CookieDict, result)


def dicts_to_cookiejar(cds: Iterable[CookieDict]):
    cj = CookieJar()
    for cd in cds:
        cj.set_cookie(Cookie(**cd))
    return cj
