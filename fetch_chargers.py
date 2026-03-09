#!/usr/bin/env python3
"""Fetch EV charger status from Enel X emobility API and save to data/chargers.json."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://emobility.enelx.com/api"
CLIENT_ID = "web-ego"
CLIENT_SECRET = "svscmkv1kdv3j2rn"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://d2jtbpdp94l0ts.cloudfront.net",
    "Referer": "https://d2jtbpdp94l0ts.cloudfront.net/",
    "User-Agent": (
        "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    ),
}

DATA_DIR = Path(__file__).parent / "data"
TOKEN_FILE = DATA_DIR / "token.json"
CHARGERS_FILE = DATA_DIR / "chargers.json"
MAX_HISTORY = 25920  # 90 days at 5-min intervals


def get_token() -> str:
    """Return a valid guest bearer token, refreshing if expired."""
    if TOKEN_FILE.exists():
        cached = json.loads(TOKEN_FILE.read_text())
        if cached.get("expires_at", 0) > time.time() + 60:
            return cached["access_token"]

    resp = requests.post(
        f"{BASE_URL}/authentication/v1/oauth/login/",
        params={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
        headers=HEADERS,
        json={"email": "guest@guest.com", "password": "guest"},
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()["result"]

    TOKEN_FILE.write_text(
        json.dumps({
            "access_token": result["access_token"],
            "expires_at": time.time() + result["expires_in"] - 60,
        })
    )
    return result["access_token"]


def fetch_station(station_id: str, token: str) -> dict:
    headers = {**HEADERS, "Authorization": f"bearer {token}"}
    resp = requests.get(
        f"{BASE_URL}/emobility/v2/charging/station/{station_id}",
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["result"]


def parse_station(raw: dict) -> dict:
    return {
        "id": raw["serialNumber"],
        "name": raw.get("csName") or raw.get("poiPartnerName", ""),
        "city": raw.get("city", ""),
        "street": raw.get("street", ""),
        "status": raw.get("status", "UNKNOWN"),
        "fastCharge": raw.get("fastCharge", False),
        "power": raw.get("csPwmAvailable", 0),
        "evses": [
            {
                "evseId": evse["evseId"],
                "status": evse.get("status", "UNKNOWN"),
                "plugs": [
                    {
                        "plugId": plug["plugId"],
                        "typology": plug.get("typology", ""),
                        "maxPower": plug.get("maxPower", 0),
                        "price": plug.get("price", 0),
                        "currency": plug.get("currency", "EUR"),
                        "typePrice": plug.get("typePrice", ""),
                        "status": plug.get("status", "UNKNOWN"),
                    }
                    for plug in evse.get("plugs", [])
                ],
            }
            for evse in raw.get("evses", [])
        ],
    }


def main():
    station_ids = [
        os.environ["CHARGER_1_ID"],
        os.environ["CHARGER_2_ID"],
    ]

    DATA_DIR.mkdir(exist_ok=True)

    token = get_token()
    now = datetime.now(timezone.utc).isoformat()

    stations = []
    for sid in station_ids:
        raw = fetch_station(sid, token)
        station = parse_station(raw)
        station["lastUpdate"] = now
        stations.append(station)

    existing = json.loads(CHARGERS_FILE.read_text()) if CHARGERS_FILE.exists() else {"history": []}

    history = existing.get("history", [])
    history.append({
        "timestamp": now,
        "stations": [
            {
                "id": s["id"],
                "status": s["status"],
                "evses": [
                    {
                        "evseId": e["evseId"],
                        "status": e["status"],
                        "price": e["plugs"][0]["price"] if e["plugs"] else None,
                        "currency": e["plugs"][0]["currency"] if e["plugs"] else None,
                        "typePrice": e["plugs"][0]["typePrice"] if e["plugs"] else None,
                    }
                    for e in s["evses"]
                ],
            }
            for s in stations
        ],
    })
    history = history[-MAX_HISTORY:]

    CHARGERS_FILE.write_text(
        json.dumps({"stations": stations, "history": history, "lastUpdate": now}, indent=2, ensure_ascii=False)
    )
    print(f"[{now}] Updated {len(stations)} stations")


if __name__ == "__main__":
    main()
