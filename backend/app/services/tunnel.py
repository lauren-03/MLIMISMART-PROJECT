"""Public HTTPS address for the SMS and USSD gateways (Cloudflare quick tunnel)."""
import asyncio
import logging
import re
import shutil
from pathlib import Path

from ..config import settings

log = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
LOCAL_COPY = Path(__file__).resolve().parents[2] / "tools" / "cloudflared.exe"

_process: asyncio.subprocess.Process | None = None
_url: str = ""


def public_url() -> str:
    """The address gateways should call: the .env value, or the tunnel's."""
    return (settings.public_url or _url).rstrip("/")


def _binary() -> str | None:
    if LOCAL_COPY.exists():
        return str(LOCAL_COPY)
    return shutil.which("cloudflared")


async def start(port: int = 8000) -> str:
    """Start `cloudflared tunnel --url` and wait for its trycloudflare address."""
    global _process, _url
    if settings.public_url or not settings.start_tunnel:
        return public_url()
    binary = _binary()
    if not binary:
        log.warning("START_TUNNEL is on but cloudflared was not found")
        return ""
    _process = await asyncio.create_subprocess_exec(
        binary, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    try:
        async with asyncio.timeout(60):
            while line := await _process.stdout.readline():
                found = URL_PATTERN.search(line.decode(errors="ignore"))
                if found:
                    _url = found.group(0)
                    break
    except TimeoutError:
        log.warning("Cloudflare tunnel did not report an address in time")
    if _url:
        log.info("Public address: %s", _url)
        asyncio.create_task(_drain())
    return _url


async def _drain() -> None:
    # Keep reading cloudflared's output so its pipe never fills up.
    while _process and _process.stdout and await _process.stdout.readline():
        pass


async def stop() -> None:
    if _process and _process.returncode is None:
        _process.terminate()
        try:
            await asyncio.wait_for(_process.wait(), 10)
        except TimeoutError:
            _process.kill()
