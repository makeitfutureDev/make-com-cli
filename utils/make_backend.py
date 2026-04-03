"""Make.com API v2 HTTP client."""
import os
import requests
from typing import Any, Optional

ZONES = ["eu1", "eu2", "us1", "us2"]


class MakeAPIError(Exception):
    def __init__(self, status_code: int, message: str, detail: dict = None):
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(f"HTTP {status_code}: {message}")


class MakeClient:
    def __init__(self, token: str, zone: str = "eu1"):
        if zone not in ZONES:
            raise ValueError(f"Invalid zone '{zone}'. Must be one of: {ZONES}")
        self.token = token
        self.zone = zone
        self.base_url = f"https://{zone}.make.com/api/v2"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Token {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", 30)
        try:
            resp = self.session.request(method, url, **kwargs)
        except requests.ConnectionError as e:
            raise MakeAPIError(0, f"Connection error: {e}")
        if not resp.ok:
            try:
                err_body = resp.json()
                msg = err_body.get("message", resp.text)
            except Exception:
                err_body = {}
                msg = resp.text
            raise MakeAPIError(resp.status_code, msg, err_body)
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    def switch_zone(self, zone: str):
        """Re-point the client to a different zone.

        Accepts zone prefixes (eu1), full hostnames (eu1.make.com),
        or Celonis hostnames (eu1.make.celonis.com).
        """
        # Full hostname — use as-is for the base URL
        if "." in zone:
            host = zone.rstrip("/")
            for z in ZONES:
                if zone.startswith(z):
                    self.zone = z
                    self.base_url = f"https://{host}/api/v2"
                    return
            return  # unrecognised host — leave as-is

        # Short zone prefix
        if zone in ZONES:
            self.zone = zone
            self.base_url = f"https://{zone}.make.com/api/v2"

    def get(self, path: str, params: dict = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, data: dict = None, params: dict = None) -> Any:
        return self._request("POST", path, json=data, params=params)

    def patch(self, path: str, data: dict) -> Any:
        return self._request("PATCH", path, json=data)

    def put(self, path: str, data: dict = None) -> Any:
        return self._request("PUT", path, json=data)

    def delete(self, path: str, params: dict = None) -> Any:
        return self._request("DELETE", path, params=params)

    def paginate(self, path: str, key: str, params: dict = None, limit: int = 100) -> list:
        """Auto-paginate through all results for a list endpoint."""
        params = dict(params or {})
        params["pg[limit]"] = limit
        params["pg[offset]"] = 0
        results = []
        while True:
            data = self.get(path, params=params)
            page = data.get(key, [])
            results.extend(page)
            if len(page) < limit:
                break
            params["pg[offset]"] += limit
        return results
