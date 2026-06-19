"""~/.make-cli/config.yaml management."""
import os
import yaml
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".make-cli"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Maps a platform name to its host template. The {zone} placeholder is
# replaced at runtime; platforms whose host does not vary by zone omit it.
PLATFORM_HOSTS = {
    "make": "{zone}.make.com",
    "boost.space": "integrator.boost.space",
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f) or {}
    return {}


def save_config(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


def get_token(override: Optional[str] = None) -> Optional[str]:
    if override:
        return override
    env = os.environ.get("MAKE_API_TOKEN")
    if env:
        return env
    cfg = load_config()
    return cfg.get("api_token")


def get_zone(override: Optional[str] = None) -> str:
    if override:
        return override
    env = os.environ.get("MAKE_ZONE")
    if env:
        return env
    cfg = load_config()
    return cfg.get("zone", "eu1")


def get_platform(override: Optional[str] = None) -> str:
    if override:
        return override
    env = os.environ.get("MAKE_PLATFORM")
    if env:
        return env
    cfg = load_config()
    return cfg.get("platform", "make")


def get_base_url(platform: str, zone: str) -> str:
    """Resolve the full API base URL from a (platform, zone) pair.

    Known platforms use their host template from PLATFORM_HOSTS. Unknown
    platform values are treated as a literal custom hostname.
    """
    template = PLATFORM_HOSTS.get(platform, platform)
    host = template.format(zone=zone) if "{zone}" in template else template
    return f"https://{host}/api/v2"
