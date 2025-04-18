from aiohttp.client import ClientSession

from hdupy._abc import AbstractHduModule

from .modules import MODULES, Login


class EduSys(AbstractHduModule):
    login: Login

    def __init__(self, session: ClientSession):
        super().__init__(session)

        for m in MODULES:
            setattr(self, m.__name__.lower(), m(session))
