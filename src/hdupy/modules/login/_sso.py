import base64

from aiohttp import ClientSession
from Crypto.Cipher import DES
from Crypto.Util import Padding
from lxml import etree

from hdupy.utils.headers import get_headers


class SSODependencyMixin:
    _API_SSO_LOGIN = "https://sso.hdu.edu.cn/login"

    @classmethod
    async def _get_flowkey_crypto(cls, session: ClientSession):
        async with session.get(
            cls._API_SSO_LOGIN, headers=get_headers({"Referer": cls._API_SSO_LOGIN})
        ) as resp:
            resp.raise_for_status()
            return cls._extract_flowkey_crypto(await resp.text("utf-8"))

    @staticmethod
    def _extract_flowkey_crypto(source: str | bytes):
        elem = etree.HTML(source)
        flowkey = elem.xpath('//*[@id="login-page-flowkey"]/text()')
        crypto = elem.xpath('//*[@id="login-croypto"]/text()')
        if flowkey and crypto:
            return str(flowkey[0]), str(crypto[0])
        return None

    @staticmethod
    def _encrypt_password_des(crypto: str, password: str):
        cipher = DES.new(base64.b64decode(crypto), DES.MODE_ECB)
        encrypted_password = cipher.encrypt(
            Padding.pad(password.encode("utf-8"), DES.block_size, style="pkcs7")
        )
        return base64.b64encode(encrypted_password).decode("utf-8")
