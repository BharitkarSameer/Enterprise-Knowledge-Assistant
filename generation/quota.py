"""
Local Gemini free-tier guard (RPM / RPD).

Matches typical Gemini 2.5 Flash free limits:
  RPM 5, TPM 250K (not enforced here — prompts are small), RPD 20.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import date
from pathlib import Path

from fastapi import HTTPException

# Free-tier defaults for gemini-2.5-flash (override via .env)
DEFAULT_RPM = 5
DEFAULT_RPD = 20

_STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "gemini_quota.json"
_lock = asyncio.Lock()
_minute_times: list[float] = []
_day_key: str | None = None
_day_count = 0
_loaded = False


def _limits() -> tuple[int, int]:
    rpm = int(os.getenv("GEMINI_RPM", str(DEFAULT_RPM)))
    rpd = int(os.getenv("GEMINI_RPD", str(DEFAULT_RPD)))
    return max(1, rpm), max(1, rpd)


def _today() -> str:
    return date.today().isoformat()


def _load_state() -> None:
    global _day_key, _day_count, _loaded
    if _loaded:
        return
    _loaded = True
    try:
        raw = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
        _day_key = str(raw.get("day") or "")
        _day_count = int(raw.get("count") or 0)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        _day_key = _today()
        _day_count = 0


def _save_state() -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(
        json.dumps({"day": _day_key, "count": _day_count}, indent=2),
        encoding="utf-8",
    )


def _roll_day() -> None:
    global _day_key, _day_count
    today = _today()
    if _day_key != today:
        _day_key = today
        _day_count = 0


async def acquire_gemini_slot() -> None:
    """
    Wait for an RPM slot, or fail fast if the daily free-tier cap is used.
    Call this once per real Gemini request (including retries).
    """
    global _day_count
    import time

    while True:
        wait_for = 0.0
        async with _lock:
            _load_state()
            _roll_day()
            rpm, rpd = _limits()

            if _day_count >= rpd:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        f"Local free-tier daily cap reached ({_day_count}/{rpd} RPD). "
                        "Wait until tomorrow, raise GEMINI_RPD if your quota increased, "
                        "or use a different API key / paid plan."
                    ),
                )

            now = time.monotonic()
            window = [t for t in _minute_times if now - t < 60.0]
            _minute_times.clear()
            _minute_times.extend(window)

            if len(_minute_times) >= rpm:
                wait_for = 60.0 - (now - _minute_times[0]) + 0.25
            else:
                _minute_times.append(now)
                _day_count += 1
                _save_state()
                return

        if wait_for > 0:
            await asyncio.sleep(wait_for)


def mark_daily_exhausted() -> None:
    """Align local RPD counter with a Google daily-quota 429."""
    global _day_count
    _load_state()
    _roll_day()
    _, rpd = _limits()
    _day_count = rpd
    _save_state()


def quota_status() -> dict:
    _load_state()
    _roll_day()
    rpm, rpd = _limits()
    return {
        "rpm_limit": rpm,
        "rpd_limit": rpd,
        "rpd_used": _day_count,
        "rpd_remaining": max(0, rpd - _day_count),
        "day": _day_key or _today(),
    }
