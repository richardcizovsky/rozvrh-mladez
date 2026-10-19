#!/usr/bin/env python3
"""Přihlásí se do CVF API, stáhne data klubu a uloží je do club.json.

Přihlašovací údaje se berou jen z proměnných prostředí API_USERNAME a API_PASSWORD.
Token žije jen v paměti procesu – nikdy se nevypisuje ani neukládá.
Bez externích závislostí; pomocné funkce se sdílejí s fetch_team.py.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fetch_team import BASE, CLUB_ID, describe_keys, die, extract_token, request

OUT = Path(__file__).resolve().parent.parent / "club.json"


def main():
    login = os.environ.get("API_USERNAME")
    password = os.environ.get("API_PASSWORD")
    if not login or not password:
        die("chybí API_USERNAME nebo API_PASSWORD")

    token = extract_token(request(f"{BASE}/auth/login", {"login": login, "password": password}))
    if not token:
        die("v odpovědi na přihlášení nebyl nalezen token")
    print(f"::add-mask::{token}")  # pojistka: GitHub Actions token v logu zamaskuje

    data = request(f"{BASE}/club/{CLUB_ID}", token=token)
    if not isinstance(data, dict):
        data = {"data": data}
    # Do logu jen NÁZVY klíčů (ne hodnoty) – pro diagnostiku struktury
    print(f"Struktura odpovědi: {describe_keys(data)}")

    # Čas aktualizace se zapisuje jen při skutečné změně dat (jinak by se commitovalo pořád)
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
        except ValueError:
            old = {}
    old_updated = old.pop("updated", None)
    if old_updated and old == data:
        print("Beze změny, nic se neukládá")
        return
    data["updated"] = datetime.now(ZoneInfo("Europe/Prague")).isoformat(timespec="minutes")
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(f"Uloženo do {OUT.name}")


if __name__ == "__main__":
    main()

