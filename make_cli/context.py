"""Shared CLI context passed via Click's obj parameter."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CliContext:
    json_mode: bool = False
    _token: Optional[str] = field(default=None, repr=False)
    _zone: str = field(default="eu1", repr=False)
    _client: object = field(default=None, repr=False)

    @property
    def client(self):
        if self._client is None:
            from utils.make_backend import MakeClient
            if not self._token:
                raise RuntimeError(
                    "No API token configured. Run: make-cli config set api_token <token>"
                )
            self._client = MakeClient(token=self._token, zone=self._zone)
        return self._client

    def use_org_zone(self, org_id: int):
        """Switch the client zone to match the org's actual zone.
        First tries a direct GET; falls back to scanning the org list.
        Safe to call before any org-scoped API operations.
        """
        from utils.make_backend import MakeAPIError
        zone = None
        try:
            data = self.client.get(f"/organizations/{org_id}")
            zone = data.get("organization", data).get("zone", "")
        except MakeAPIError:
            # Direct GET not permitted — scan org list instead
            try:
                data = self.client.get("/organizations")
                for o in data.get("organizations", []):
                    if o.get("id") == org_id:
                        zone = o.get("zone", "")
                        break
            except MakeAPIError:
                pass
        if zone:
            self.client.switch_zone(zone)
