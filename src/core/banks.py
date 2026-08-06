from typing import Any, TypedDict
from data.banks_json import load_banks_json


class BankItem(TypedDict):
    code: str
    name: str
    short_name: str
    bin: str
    logo: str


_BANKS_CACHE: list[BankItem] | None = None
_BANKS_MAP: dict[str, BankItem] | None = None


def get_banks_list() -> list[BankItem]:
    """
    Returns the list of Vietnamese banks loaded via data.banks_json module.
    """
    global _BANKS_CACHE, _BANKS_MAP
    if _BANKS_CACHE is None:
        raw_banks = load_banks_json()
        _BANKS_CACHE = [
            BankItem(
                code=b["code"],
                name=b["name"],
                short_name=b["short_name"],
                bin=b.get("bin", ""),
                logo=b.get("logo", ""),
            )
            for b in raw_banks
        ]
        _BANKS_MAP = {b["code"].upper(): b for b in _BANKS_CACHE}

    return _BANKS_CACHE


def get_bank_by_code(bank_code: str | None) -> BankItem | None:
    """
    Looks up a bank by its bank_code (case-insensitive).
    """
    if not bank_code:
        return None
    get_banks_list()  # Ensures cache populated
    assert _BANKS_MAP is not None
    return _BANKS_MAP.get(bank_code.strip().upper())


def get_bank_name_by_code(bank_code: str | None) -> str | None:
    """
    Returns the full bank name for a given bank_code, or None if not found.
    """
    bank = get_bank_by_code(bank_code)
    return bank["name"] if bank else None



