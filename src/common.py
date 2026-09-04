
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
    if not value or not str(value).strip():
        return None
    val = str(value).strip().split("T")[0].split(" ")[0]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d %b %Y", "%d-%m-%Y", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            pass
    return None

def date_distance(a: str, b: str) -> int:
    da = parse_date(a)
    db = parse_date(b)
    if not da or not db:
        return 999
    return abs((da - db).days)
