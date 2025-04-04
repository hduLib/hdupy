from abc import ABC

from aiohttp.client import ClientSession


class AbstractHduModule(ABC):
    def __init__(self, session: ClientSession):
        self._session = session

    @property
    def session(self) -> ClientSession:
        return self._session
