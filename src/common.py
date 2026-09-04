
from __future__ import annotations
import re
from datetime import datetime

def to_int_amount(value) -> int:
    if value in (None, ""): return 0
    return int(round(float(str(value).strip().replace(",",""))))

def norm_ref(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())

def norm_name(value: str) -> str:
    value=(value or "").upper()
    value=re.sub(r"\b(PVT|PRIVATE|LTD|LIMITED|LLP|INC|CO|COMPANY)\b","",value)
    return re.sub(r"[^A-Z0-9]","",value)

def parse_date(value: str):
    for fmt in ("%Y-%m-%d","%d/%m/%Y","%d %b %Y","%d-%m-%Y"):
        try: return datetime.strptime(value.strip(),fmt).date()
        except ValueError: pass
    raise ValueError(f"Unsupported date format: {value!r}")

def date_distance(a: str,b: str) -> int:
    return abs((parse_date(a)-parse_date(b)).days)
