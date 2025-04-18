from aiohttp import ClientSession
from yarl import URL

from hdupy._abc import AbstractHduModule


class AbstractHduEduSysModule(AbstractHduModule):
    MODULE_CODE: str | None = None  # child class should override this

    def __init__(
        self, session: ClientSession, base_url: str = "https://newjw.hdu.edu.cn"
    ):
        super().__init__(session)
        self._base_url = base_url

    def _get_url(self, path: str, append_module_code=True):
        url = URL(self._base_url) / path.removeprefix("/")
        if append_module_code:
            if self.MODULE_CODE is None:
                raise NotImplementedError
            url %= {"gnmkdm": self.MODULE_CODE}
            # 功能模块代码  说是
            # g n m k d m

        return url
