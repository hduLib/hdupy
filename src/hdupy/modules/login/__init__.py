import base64
import hashlib
import random
import string
from dataclasses import dataclass
from enum import Enum
from typing import cast

from hdupy._abc import AbstractHduModule
from hdupy.utils.headers import get_headers
from hdupy.utils.templates import (
    RequestOptions,
    get_preset_result_handler,
    request_template,
)

from ._newjw import NewjwDependencyMixin
from ._sso import SSODependencyMixin

__all__ = ["Login"]


class Login(AbstractHduModule, NewjwDependencyMixin, SSODependencyMixin):
    __hdumodule_name__ = "login"

    class LoginException(Exception):
        """exception for login"""

    class PreconditionFailed(LoginException):
        """raise when failed to get flowkey or crypto"""

    class LoginFailed(LoginException):
        """raise when failed to login"""

    async def login_edusys(self, username: str, password: str) -> None:
        """may has no effect"""
        pubkey = await self._get_pubkey(self._session)
        csrftoken = await self._get_csrftoken(self._session)
        if csrftoken is None:
            raise self.PreconditionFailed
        payload = {
            "csrftoken": csrftoken,
            "language": "zh_CN",
            "ydType": "",
            "yhm": username,
            "mm": self._encrypt_password_rsa(pubkey, password),
        }
        async with self._session.post(
            self._API_NEWJW_LOGIN, data=payload, headers=get_headers()
        ) as resp:
            resp.raise_for_status()
            if resp.url.parts[-1] == "login_slogin.html":
                raise self.LoginFailed

    async def login_sso(self, username: str, password: str):
        if _ := await self._get_flowkey_crypto(self._session):
            flowkey, crypto = _
        else:
            raise self.PreconditionFailed
        payload = {
            "username": username,
            "passwordPre": password,
            "type": "UsernamePassword",
            "_eventId": "submit",
            "geolocation": "",
            "execution": flowkey,
            "captcha_code": "",
            "croypto": crypto,  # typo lmao
            "password": self._encrypt_password_des(crypto, password),
        }
        async with self._session.post(
            self._API_SSO_LOGIN,
            headers=get_headers({"Referer": str(self._API_SSO_LOGIN)}),
            data=payload,
        ) as resp:
            resp.raise_for_status()
            if resp.host == "sso.hdu.edu.cn":
                raise self.LoginFailed

    @dataclass
    class QrLoginSession:
        class QrLoginStatus(Enum):
            PENDING = 0
            OK = 1
            TIMEOUT = 2

        csrf_key: str | None = None
        csrf_value: str | None = None
        login_id: str | None = None
        status: QrLoginStatus = QrLoginStatus.PENDING

    @staticmethod
    def _generate_csrf_value(k: str) -> str:
        k_b64 = base64.b64encode(k.encode()).decode()
        output = k_b64[: len(k_b64) // 2] + k_b64 + k_b64[len(k_b64) // 2 :]
        return hashlib.md5(output.encode()).hexdigest()

    @classmethod
    def qrlogin_generate_csrf(cls):
        csrf_key = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        csrf_value = cls._generate_csrf_value(csrf_key)
        return csrf_key, csrf_value

    @request_template(get_preset_result_handler("json"))
    def qrlogin_get_login_id(self, csrf_key: str, csrf_value: str):
        return "https://sso.hdu.edu.cn/api/protected/qrlogin/loginid", cast(
            RequestOptions,
            {"headers": {"Csrf-Key": csrf_key, "Csrf-Value": csrf_value}},
        )

    @request_template(get_preset_result_handler("bytes"))
    def qrlogin_get_login_qrcode(self, login_id: str):
        return f"https://sso.hdu.edu.cn/api/public/qrlogin/qrgen/{login_id}/dingDingQr"

    @request_template(get_preset_result_handler("json"))
    def qrlogin_get_login_result(self, csrf_key: str, csrf_value: str, login_id: str):
        return f"https://sso.hdu.edu.cn/api/protected/qrlogin/scan/{login_id}", cast(
            RequestOptions,
            {"headers": {"Csrf-Key": csrf_key, "Csrf-Value": csrf_value}},
        )

    async def qrlogin_submit_login(self, result_token: str):
        _ = await self._get_flowkey_crypto(self._session)
        if _ is None:
            raise self.PreconditionFailed
        flowkey, _ = _
        payload = {
            "username": result_token,
            "type": "dingDingQr",
            "_eventId": "submit",
            "geolocation": "",
            "execution": flowkey,
        }
        async with self._session.post(
            self._API_SSO_LOGIN,
            params=payload,
            headers=get_headers({"Referer": str(self._API_SSO_LOGIN)}),
        ) as resp:
            resp.raise_for_status()
            if "用户名密码登录" in await resp.text("utf-8"):
                raise self.LoginFailed

    async def qrlogin_flow(self):
        ck, cv = self.qrlogin_generate_csrf()
        _ = await self.qrlogin_get_login_id(ck, cv)  # pyright: ignore[reportCallIssue]
        if _["code"] != 200:
            raise self.PreconditionFailed
        lid: str = _["data"]
        yield await self.qrlogin_get_login_qrcode(lid)  # pyright: ignore[reportCallIssue]
        _ = await self.qrlogin_get_login_result(ck, cv, lid)  # pyright: ignore[reportCallIssue]
        if _["code"] != 200:
            raise self.LoginFailed(_)
        token = _["data"]
        await self.qrlogin_submit_login(token)

    async def check_edusys_login(self):
        async with self._session.get(
            "https://newjw.hdu.edu.cn/jwglxt/xtgl/index_initMenu.html"
        ) as resp:
            return resp.url.parts[-1] != "login_slogin.html"

    async def login_edusys_via_sso(self):
        async with self._session.get(
            "https://newjw.hdu.edu.cn/sso/driot4login"
        ) as resp:
            if resp.url.parts[-1] != "index_initMenu.html":
                raise self.LoginFailed
