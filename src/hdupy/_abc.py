from abc import ABC
from contextlib import asynccontextmanager
from typing import Any, Literal

from aiohttp.client import ClientSession
from yarl import URL, Query

from .utils.headers import LooseHeaders, get_headers


class AbstractHduModule(ABC):
    def __init__(self, session: ClientSession):
        self._session = session

    @property
    def session(self) -> ClientSession:
        return self._session

    @asynccontextmanager
    async def _request(
        self,
        method: Literal["GET", "POST"],
        url: str | URL,
        params: Query = None,
        data: Any = None,
        json: Any = None,
        headers: LooseHeaders | None = None,
    ):
        headers = get_headers(headers)
        async with self._session.request(
            method,
            url,
            params=params,
            data=data,
            json=json,
            headers=headers,
            raise_for_status=True,
            allow_redirects=True,
        ) as resp:
            # maybe more options here
            yield resp
