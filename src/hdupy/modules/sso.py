import base64
import hashlib
import secrets
import string

from Crypto.Cipher import DES
from Crypto.Util import Padding
from lxml import etree

from hdupy._abc import AbstractHduModule
from hdupy.utils.headers import get_headers


class SSOFailed(Exception):
    pass


class SSO(AbstractHduModule):
    _API_SSO_LOGIN = "https://sso.hdu.edu.cn/login"

    async def _get_flowkey_crypto(self):
        async with self._request(
            "GET", self._API_SSO_LOGIN, headers={"Referer": self._API_SSO_LOGIN}
        ) as resp:
            return self._extract_flowkey_crypto(await resp.text("utf-8"))

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

    async def login(self, username: str, password: str):
        if _ := await self._get_flowkey_crypto():
            flowkey, crypto = _
        else:
            raise SSOFailed("failed to get flowkey or crypto")
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
        async with self._request(
            "POST",
            self._API_SSO_LOGIN,
            headers={"Referer": str(self._API_SSO_LOGIN)},
            data=payload,
        ) as resp:
            if resp.host == "sso.hdu.edu.cn":
                raise SSOFailed(f"wrong redirect destination: {resp.url}")

    @staticmethod
    def _generate_csrf_value(k: str) -> str:
        k_b64 = base64.b64encode(k.encode()).decode()
        output = k_b64[: len(k_b64) // 2] + k_b64 + k_b64[len(k_b64) // 2 :]
        return hashlib.md5(output.encode()).hexdigest()

    @classmethod
    def qrlogin_generate_csrf(cls):
        csrf_key = "".join(
            [secrets.choice(string.ascii_letters + string.digits) for _ in range(32)]
        )
        # csrf_key = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        csrf_value = cls._generate_csrf_value(csrf_key)
        return csrf_key, csrf_value

    async def qrlogin_get_login_id(self, csrf_key: str, csrf_value: str):
        async with self._request(
            "GET",
            "https://sso.hdu.edu.cn/api/protected/qrlogin/loginid",
            headers={"Csrf-Key": csrf_key, "Csrf-Value": csrf_value},
        ) as resp:
            return await resp.json(encoding="utf-8")

    async def qrlogin_get_login_qrcode(self, login_id: str):
        async with self._request(
            "GET",
            f"https://sso.hdu.edu.cn/api/public/qrlogin/qrgen/{login_id}/dingDingQr",
        ) as resp:
            return await resp.read()

    async def qrlogin_get_login_result(
        self, csrf_key: str, csrf_value: str, login_id: str
    ):
        async with self._request(
            "GET",
            f"https://sso.hdu.edu.cn/api/protected/qrlogin/scan/{login_id}",
            headers={"Csrf-Key": csrf_key, "Csrf-Value": csrf_value},
        ) as resp:
            return await resp.json(encoding="utf-8")

    async def qrlogin_submit_login(self, result_token: str):
        _ = await self._get_flowkey_crypto()
        if _ is None:
            raise SSOFailed("failed to get flowkey or crypto")
        flowkey, _ = _
        payload = {
            "username": result_token,
            "type": "dingDingQr",
            "_eventId": "submit",
            "geolocation": "",
            "execution": flowkey,
        }
        async with self._request(
            "POST",
            self._API_SSO_LOGIN,
            params=payload,
            headers={"Referer": str(self._API_SSO_LOGIN)},
        ) as resp:
            if "用户名密码登录" in await resp.text("utf-8"):
                raise SSOFailed("failure sign found")

    async def qrlogin_flow(self):
        ck, cv = self.qrlogin_generate_csrf()
        _ = await self.qrlogin_get_login_id(ck, cv)
        if _["code"] != 200:
            raise SSOFailed(_)
        lid: str = _["data"]
        yield await self.qrlogin_get_login_qrcode(lid)
        _ = await self.qrlogin_get_login_result(ck, cv, lid)
        if _["code"] != 200:
            raise SSOFailed(_)
        token = _["data"]
        await self.qrlogin_submit_login(token)
