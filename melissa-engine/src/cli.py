import asyncio
import json
import os
import sys
import time
from pathlib import Path

from src.runtime.loader import post_json, get_base_url, save_device_info

# Настройки ожидания:
#   MELISSA_LINK_TIMEOUT_SEC     — общий таймаут ожидания (сек), по умолчанию 180
#   MELISSA_LINK_POLL_INTERVAL   — интервал опроса (сек), по умолчанию 2
LINK_TIMEOUT_SEC = int(os.getenv("MELISSA_LINK_TIMEOUT_SEC", "180"))
POLL_INTERVAL = float(os.getenv("MELISSA_LINK_POLL_INTERVAL", "2.0"))

DEVICE_FILE = Path(os.getenv("MELISSA_DEVICE_FILE", str(Path.home() / ".melissa" / "device.json")))

USAGE = """Usage:
  melissa link            # register & activate device
  melissa sync            # fetch artifacts for this device
  melissa                 # (legacy demo) compile sample bundle
"""


async def cmd_link() -> None:
    base = get_base_url()
    # 1) Регистрация устройства
    info = await post_json(f"{base}/v1/devices/register", {})
    device_id = info.get("device_id")
    user_code = info.get("user_code")
    verification_uri = info.get("verification_uri") or f"{base}/link"

    if not device_id or not user_code:
        print("Registration response is missing device_id or user_code.")
        print("Got:", json.dumps(info, ensure_ascii=False, indent=2))
        sys.exit(1)

    print(f"🔗 Device ID: {device_id}")
    print("➡️  Go to:", verification_uri)
    print("➡️  Enter user code:", user_code)
    print("⏳ Waiting for activation...")

    # 2) Ожидание активации (poll)
    t0 = time.monotonic()
    while time.monotonic() - t0 < LINK_TIMEOUT_SEC:
        try:
            poll_resp = await post_json(f"{base}/v1/devices/poll", {"device_id": device_id})
        except Exception as e:
            # Не валим процесс по временным ошибкам сети — просто подождём и повторим
            await asyncio.sleep(POLL_INTERVAL)
            continue

        status = poll_resp.get("status")
        if status == "linked":
            token = poll_resp.get("device_token")
            if not token:
                # маловероятно, но проверим
                print("⚠️  API returned 'linked' without device_token, retrying...")
                await asyncio.sleep(POLL_INTERVAL)
                continue

            # Сохраняем файл устройства
            save_device_info(device_id=device_id, device_token=token)
            print("✅ Linked! Token saved.")
            return

        # Иначе pending или что-то ещё — подождать и опросить снова
        await asyncio.sleep(POLL_INTERVAL)

    print("❌ Activation timed out")
    sys.exit(1)


async def cmd_sync() -> None:
    from src.core.sync import do_sync
    await do_sync()


async def cmd_legacy_demo() -> None:
    # старый демо-режим, если он у вас ещё есть
    from src.core.legacy_demo import run_demo
    await run_demo()


def main() -> int:
    if len(sys.argv) <= 1:
        print(USAGE)
        return 0

    cmd = sys.argv[1].lower().strip()
    if cmd == "link":
        asyncio.run(cmd_link())
        return 0
    elif cmd == "sync":
        asyncio.run(cmd_sync())
        return 0
    else:
        # совместимость со старым поведением: просто запустить демо
        asyncio.run(cmd_legacy_demo())
        return 0


if __name__ == "__main__":
    sys.exit(main())
