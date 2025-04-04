import base64
import time
from typing import TypedDict

from aiohttp import ClientSession
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from lxml import etree

from hdupy.utils.headers import get_headers


class NewjwDependencyMixin:
    _API_NEWJW_LOGIN = "https://newjw.hdu.edu.cn/jwglxt/xtgl/login_slogin.html"
    _API_NEWJW_PUBKEY = "https://newjw.hdu.edu.cn/jwglxt/xtgl/login_getPublicKey.html"

    class _PubkeyResp(TypedDict):
        modulus: str
        exponent: str

    @staticmethod
    def _encrypt_password_rsa(pubkey: _PubkeyResp, password: str):
        public_key = RSA.construct(
            (
                int.from_bytes(base64.b64decode(pubkey["modulus"])),
                int.from_bytes(base64.b64decode(pubkey["exponent"])),
            )
        )
        cipher = PKCS1_v1_5.new(public_key)
        encrypted_password = cipher.encrypt(password.encode("utf-8"))
        return base64.b64encode(encrypted_password).decode("utf-8")

    @classmethod
    async def _get_pubkey(cls, session: ClientSession) -> _PubkeyResp:
        async with session.get(
            cls._API_NEWJW_PUBKEY,
            params={"time": int(time.time())},
            headers=get_headers(),
        ) as resp:
            resp.raise_for_status()
            return await resp.json(encoding="utf-8")

    @classmethod
    async def _get_csrftoken(cls, session: ClientSession) -> str | None:
        resp = await session.get(
            cls._API_NEWJW_LOGIN,
            headers=get_headers(),
        )
        html = etree.HTML(await resp.text("utf-8"), etree.HTMLParser())
        csrftoken = html.xpath('//input[@name="csrftoken"]/@value')
        if csrftoken and (_ := csrftoken[0]):
            return _
