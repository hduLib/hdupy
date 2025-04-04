from hdupy.data.i18n import data as _I18N_TABLE


def query(kw: str, n: int = 3):
    result: list[tuple[str, str]] = []
    for k, v in _I18N_TABLE.items():
        if kw.lower() in k.lower():
            result.append((k, v))
        if len(result) >= n:
            break
    return result
