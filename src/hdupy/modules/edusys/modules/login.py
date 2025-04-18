import base64
import time
from typing import TypedDict

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from lxml import etree

from hdupy.utils.headers import get_headers

from .._edusys_abc import AbstractHduEduSysModule


class _PubkeyResp(TypedDict):
    modulus: str
    exponent: str


class LoginFailed(Exception):
    pass


class Login(AbstractHduEduSysModule):
    MODULE_CODE = "login"

    async def _get_pubkey(self) -> _PubkeyResp:
        async with self._request(
            "GET",
            self._get_url("/jwglxt/xtgl/login_getPublicKey.html"),
            params={"time": int(time.time())},
        ) as resp:
            return await resp.json(encoding="utf-8")

    async def _get_csrftoken(self) -> str | None:
        async with self._request(
            "GET",
            self._get_url("/jwglxt/xtgl/login_slogin.html"),
        ) as resp:
            html = etree.HTML(await resp.text("utf-8"), etree.HTMLParser())
            csrftoken = html.xpath('//input[@name="csrftoken"]/@value')
            if csrftoken and (_ := csrftoken[0]):
                return _

    async def login(self, username: str, password: str) -> None:
        """may has no effect"""
        pubkey = await self._get_pubkey()
        csrftoken = await self._get_csrftoken()
        if csrftoken is None:
            raise LoginFailed("csrf token not found")
        payload = {
            "csrftoken": csrftoken,
            "language": "zh_CN",
            "ydType": "",
            "yhm": username,
            "mm": self._encrypt_password_rsa(pubkey, password),
        }
        async with self._request(
            "POST",
            self._get_url("/jwglxt/xtgl/login_slogin.html"),
            data=payload,
        ) as resp:
            if resp.url.parts[-1] == "login_slogin.html":
                raise LoginFailed(f"wrong redirect destination {resp.url}")

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

    async def check_login(self):
        async with self._request(
            "GET",
            self._get_url("/jwglxt/xtgl/index_initMenu.html", append_module_code=False),
        ) as resp:
            return resp.url.parts[-1] != "login_slogin.html"

    async def login_via_sso(self):
        async with self._request(
            "GET", self._get_url("/sso/driot4login", append_module_code=False)
        ) as resp:
            if resp.url.parts[-1] != "index_initMenu.html":
                raise LoginFailed(f"wrong redirect destination: {resp.url}")
