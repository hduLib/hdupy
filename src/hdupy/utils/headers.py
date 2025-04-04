from aiohttp.typedefs import LooseHeaders
from multidict import CIMultiDict, MultiDict, MultiDictProxy

_BASIC_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Dnt": "1",
    "Priority": "u=0, i",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def get_headers(updates: LooseHeaders | None = None) -> CIMultiDict[str]:
    """from aiohttp.client, modified"""
    result = CIMultiDict(_BASIC_HEADERS)
    if updates:
        if not isinstance(updates, (MultiDictProxy, MultiDict)):
            updates = CIMultiDict(updates)
        added_names: set[str] = set()
        for key, value in updates.items():
            if key in added_names:
                result.add(key, value)
            else:
                result[key] = value
                added_names.add(key)
    return result
