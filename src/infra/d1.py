from typing import Any


def row_value(row: Any, key: str) -> Any:
    if isinstance(row, dict):
        return row.get(key)
    return getattr(row, key, None)


async def rows(statement: Any) -> list[Any]:
    result = await statement.all()
    return list(result.results or [])


async def first(statement: Any) -> Any | None:
    return await statement.first()
