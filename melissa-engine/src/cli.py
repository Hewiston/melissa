import asyncio
import pathlib
import sys
import time
import json
import yaml
from src.runtime.loader import post_json, get_bytes
from src.core.verify import verify_bundle
from src.core.schema import validate_payload_parts
from src.core.state import load_device, save_device, load_cache, save_cache, bundle_path

def _cfg():
    p = pathlib.Path(__file__).resolve().parents[1] / "melissa.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))

async def cmd_link():
    cfg = _cfg()
    base = cfg["api_base"].rstrip("/")
    # 1) register
    info = await post_json(f"{base}/v1/devices/register", {})
    device_id = info["device_id"]
    print("🔗 Device ID:", device_id)
    print("➡️  Go to:", info["verification_uri"])
    print("➡️  Enter user code:", info["user_code"])
    # 2) poll loop
    print("⏳ Waiting for activation...")
    token = None
    for _ in range(120):  # до 2 минут
        await asyncio.sleep(1)
        res = await post_json(f"{base}/v1/devices/poll", {"device_id": device_id})
        if not res.get("pending"):
            token = res.get("device_token")
            break
    if not token:
        print("❌ Activation timed out")
        return
    save_device({"device_id": device_id, "device_token": token, "linked_at": int(time.time())})
    print("✅ Linked! Token saved.")

async def cmd_sync():
    cfg = _cfg()
    base = cfg["api_base"].rstrip("/")
    dev = load_device()
    if not dev:
        print("No device linked. Run: melissa link")
        return
    token = dev["device_token"]
    device_id = dev["device_id"]

    # 1) list strategies for device
    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{base}/v1/devices/{device_id}/strategies", headers={"Authorization": f"Device {token}"})
        r.raise_for_status()
        lst = r.json()

    cache = load_cache()

    # 2) for each strategy with artifact — fetch with ETag
    for item in lst:
        sid = item["strategy_id"]
        art = item.get("artifact")
        if not art:
            print(f"- {sid}: no artifact (pinned/latest not set or no versions)")
            continue
        semver = art["semver"]
        url = base + art["url"]
        cache_key = f"{sid}:{semver}"
        etag = cache.get(cache_key, {}).get("etag")

        status, body, new_etag = await get_bytes(url, etag=etag)
        if status == 304:
            print(f"- {sid}@{semver}: 304 (cached)")
            continue
        # got 200
        bundle = json.loads(body.decode("utf-8"))
        # validate and verify
        validate_payload_parts(bundle["payload"])
        verify_bundle(bundle, cfg["public_ed25519_pubkey_b64"])
        # save to disk
        path = bundle_path(sid, semver)
        path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
        # update cache
        cache[cache_key] = {"etag": new_etag}
        print(f"- {sid}@{semver}: downloaded, verified, saved to {path}")

    save_cache(cache)
    print("✅ Sync complete")

def main():
    if len(sys.argv) == 1:
        print("Usage:")
        print("  melissa link            # register & activate device")
        print("  melissa sync            # fetch artifacts for this device")
        print("  melissa                 # (legacy demo) compile sample bundle")
        return
    if sys.argv[1] == "link":
        asyncio.run(cmd_link())
    elif sys.argv[1] == "sync":
        asyncio.run(cmd_sync())
    else:
        print("Unknown command")

if __name__ == "__main__":
    main()
