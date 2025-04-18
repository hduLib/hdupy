from aiohttp.client import ClientSession

from ._abc import AbstractHduModule
from .modules import MODULES, SSO, EduSys


class HduClient(AbstractHduModule):
    sso: SSO
    edusys: EduSys

    def __init__(self):
        super().__init__(ClientSession(raise_for_status=True))

        for m in MODULES:
            setattr(self, m.__name__.lower(), m(self._session))
