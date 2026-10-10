"""Built-in spreadsheet functions — mirrors Excel-compatible function set."""

from __future__ import annotations

from typing import Any

registry: dict[str, Any] = {}


def _register(name: str):
    def decorator(fn):
        registry[name.upper()] = fn
        return fn

    return decorator


# -- numeric aggregation --


@_register("SUM")
def fn_sum(*args: Any) -> float | None:
    total = 0.0
    for arg in args:
        flat = _flatten(arg)
        for v in flat:
            if isinstance(v, int | float):
                total += float(v)
    return total


@_register("AVERAGE")
@_register("AVG")
def fn_average(*args: Any) -> float | None:
    vals = [v for v in _flatten_all(args) if isinstance(v, int | float)]
    return sum(vals) / len(vals) if vals else None


@_register("COUNT")
def fn_count(*args: Any) -> int:
    return sum(1 for v in _flatten_all(args) if v is not None)


@_register("COUNTA")
def fn_counta(*args: Any) -> int:
    return sum(1 for v in _flatten_all(args) if v is not None and v != "")


@_register("MAX")
def fn_max(*args: Any) -> Any:
    vals = [v for v in _flatten_all(args) if isinstance(v, int | float)]
    return max(vals) if vals else None


@_register("MIN")
def fn_min(*args: Any) -> Any:
    vals = [v for v in _flatten_all(args) if isinstance(v, int | float)]
    return min(vals) if vals else None


@_register("ABS")
def fn_abs(x: Any) -> Any:
    return abs(float(x)) if x is not None else None


@_register("ROUND")
def fn_round(x: Any, n: int = 0) -> float | None:
    if x is None:
        return None
    return round(float(x), int(n))


@_register("SQRT")
def fn_sqrt(x: Any) -> float | None:
    if x is None:
        return None
    return float(float(x) ** 0.5)


@_register("POWER")
def fn_power(base: Any, exp: Any) -> float | None:
    if base is None or exp is None:
        return None
    return float(float(base) ** float(exp))


# -- text --


@_register("LEFT")
def fn_left(text: Any, n: int = 1) -> str | None:
    if text is None:
        return None
    return str(text)[: int(n)]


@_register("RIGHT")
def fn_right(text: Any, n: int = 1) -> str | None:
    if text is None:
        return None
    s = str(text)
    return s[-int(n) :] if n <= len(s) else s


@_register("MID")
def fn_mid(text: Any, start: int, length: int) -> str | None:
    if text is None:
        return None
    s = str(text)
    idx = int(start) - 1
    return s[idx : idx + int(length)]


@_register("LEN")
def fn_len(text: Any) -> int | None:
    if text is None:
        return None
    return len(str(text))


@_register("UPPER")
def fn_upper(text: Any) -> str | None:
    return str(text).upper() if text is not None else None


@_register("LOWER")
def fn_lower(text: Any) -> str | None:
    return str(text).lower() if text is not None else None


@_register("TRIM")
def fn_trim(text: Any) -> str | None:
    return str(text).strip() if text is not None else None


@_register("CONCATENATE")
@_register("CONCAT")
def fn_concat(*args: Any) -> str:
    return "".join(str(v) if v is not None else "" for v in args)


@_register("FIND")
def fn_find(sub: Any, text: Any, start: int = 1) -> int | None:
    if sub is None or text is None:
        return None
    idx = str(text).find(str(sub), int(start) - 1)
    return idx + 1 if idx >= 0 else None


@_register("REPLACE")
def fn_replace(text: Any, start: int, count: int, new_text: Any) -> str | None:
    if text is None:
        return None
    s = str(text)
    i = int(start) - 1
    return s[:i] + str(new_text) + s[i + int(count) :]


# -- logical --


@_register("IF")
def fn_if(condition: Any, true_val: Any, false_val: Any = None) -> Any:
    if condition is None:
        return false_val
    return true_val if bool(condition) else false_val


@_register("AND")
def fn_and(*args: Any) -> bool:
    return all(bool(v) for v in args if v is not None)


@_register("OR")
def fn_or(*args: Any) -> bool:
    return any(bool(v) for v in args if v is not None)


@_register("NOT")
def fn_not(x: Any) -> bool:
    return not bool(x)


@_register("TRUE")
def fn_true() -> bool:
    return True


@_register("FALSE")
def fn_false() -> bool:
    return False


# -- lookup --


@_register("VLOOKUP")
def fn_vlookup(lookup_val: Any, table: Any, col_index: int, approx: bool = False) -> Any:
    rows = _flatten_all(table) if isinstance(table, list) else [table]
    for row in rows:
        if isinstance(row, list) and len(row) >= col_index and row[0] == lookup_val:
            return row[col_index - 1]
    return None


@_register("HLOOKUP")
def fn_hlookup(lookup_val: Any, table: Any, row_index: int, approx: bool = False) -> Any:
    if not isinstance(table, list) or not table:
        return None
    headers = table[0] if isinstance(table[0], list) else []
    for i, h in enumerate(headers):
        if h == lookup_val and i + 1 < len(table):
            row = table[i + 1] if isinstance(table[i + 1], list) else []
            return row[row_index - 1] if len(row) >= row_index else None
    return None


# -- date/time placeholders --


@_register("TODAY")
def fn_today() -> str:
    from datetime import date

    return date.today().isoformat()


@_register("NOW")
def fn_now() -> str:
    from datetime import datetime

    return datetime.now().isoformat()


@_register("YEAR")
def fn_year(date_val: Any) -> int | None:
    if date_val is None:
        return None
    try:
        from datetime import datetime

        return datetime.fromisoformat(str(date_val)).year
    except Exception:
        return None


@_register("MONTH")
def fn_month(date_val: Any) -> int | None:
    if date_val is None:
        return None
    try:
        from datetime import datetime

        return datetime.fromisoformat(str(date_val)).month
    except Exception:
        return None


@_register("DAY")
def fn_day(date_val: Any) -> int | None:
    if date_val is None:
        return None
    try:
        from datetime import datetime

        return datetime.fromisoformat(str(date_val)).day
    except Exception:
        return None


# -- helpers --


def _flatten(value: Any) -> list[Any]:
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_flatten(item))
        return result
    return [value]


def _flatten_all(values: tuple[Any, ...] | list[Any]) -> list[Any]:
    result = []
    for v in values:
        result.extend(_flatten(v))
    return result
