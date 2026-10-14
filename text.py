"""Display-text helpers."""


def clean(v):
    """Hide NULLs and the database's placeholder values."""
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s in ("(Unknown)", "(None)", "[uncategorized]", "Unknown") else s


def year_text(y):
    """The database uses 99xx ids for 'unknown year'; only real years are shown."""
    return str(y) if isinstance(y, int) and 1970 <= y <= 2100 else ""
