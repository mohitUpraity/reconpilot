from __future__ import annotations
import os
from typing import Any
import requests

class RazorpayConfigError(RuntimeError):
    pass

class RazorpayClient:
    def __init__(self, key_id: str|None=None, key_secret: str|None=None):
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET")
        if not self.key_id or not self.key_secret:
            raise RazorpayConfigError("Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET for Test Mode.")

    def _get(self, path: str, params: dict[str, Any]|None=None):
        base = os.getenv("RAZORPAY_API_BASE_URL", "https://api.razorpay.com/v1").rstrip("/")
        response = requests.get(
            f"{base}/{path.lstrip('/')}", params=params,
            auth=(self.key_id, self.key_secret), timeout=20
        )
        response.raise_for_status()
        return response.json()

    def fetch_payments(self, count=100, skip=0):
        return self._get("payments", {"count": max(1,min(int(count),100)), "skip": max(0,int(skip))})

    def fetch_all_payments(self, page_size=100):
        items=[]
        skip=0
        while True:
            page=self.fetch_payments(page_size, skip)
            batch=page.get("items", [])
            items.extend(batch)
            if len(batch) < page_size:
                break
            skip += len(batch)
        return items

    def fetch_settlements(self, count=100, skip=0):
        return self._get("settlements", {"count": max(1,min(int(count),100)), "skip": max(0,int(skip))})

    def fetch_all_settlements(self, page_size=100):
        items=[]
        skip=0
        while True:
            page=self.fetch_settlements(page_size, skip)
            batch=page.get("items", [])
            items.extend(batch)
            if len(batch) < page_size:
                break
            skip += len(batch)
        return items

    def fetch_settlement_recon(self, year: int, month: int, day: int|None=None, count=1000, skip=0):
        params = {"year": year, "month": month, "count": max(1,min(int(count),1000)), "skip": max(0,int(skip))}
        if day is not None:
            params["day"] = day
        return self._get("settlements/recon/combined", params)
