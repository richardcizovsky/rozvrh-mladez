#!/usr/bin/env python3
"""Přihlásí se do CVF API, stáhne data týmu a uloží je do team.json bez kontaktních údajů.

Přihlašovací údaje se berou jen z proměnných prostředí API_USERNAME a API_PASSWORD.
Token žije jen v paměti procesu – nikdy se nevypisuje ani neukládá.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://api.cvf.1webit.cz/api/v1"
SEASON = "2026/27"
CLUB_ID = "10000165"
OUT = Path(__file__).resolve().parent.parent / "team.json"

# Klíče obsahující kontaktní / osobní údaje se z výstupu odstraní
CONTACT_RE = re.compile(
    r"(contact|kontakt|e-?mail|phone|telefon|mobil|mobile|tel$|address|adres|"
    r"street|ulice|zip|psc|birth|narozen)",
    re.IGNORECASE,
)


def die(msg):
    # Nikdy nevypisujeme tělo odpovědi ani hlavičky – mohly by obsahovat token.
    print(f"Chyba: {msg}", file=sys.stderr)
    sys.exit(1)


def request(url, data=None, token=None):
    headers = {"accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        die(f"HTTP {e.code} při volání {url.split('?')[0]}")
    except Exception as e:
        die(f"{type(e).__name__} při volání {url.split('?')[0]}")


def extract_token(resp):
    """Vrátí accessToken z odpovědi na přihlášení."""
    if isinstance(resp, dict):
        if isinstance(resp.get("accessToken"), str):
            return resp["accessToken"]
    return None


def strip_contacts(obj):
    if isinstance(obj, dict):
        return {k: strip_contacts(v) for k, v in obj.items() if not CONTACT_RE.search(k)}
    if isinstance(obj, list):
        return [strip_contacts(v) for v in obj]
    return obj


def main():
    login = os.environ.get("API_USERNAME")
    password = os.environ.get("API_PASSWORD")
    if not login or not password:
        die("chybí API_USERNAME nebo API_PASSWORD")

    token = extract_token(request(f"{BASE}/auth/login", {"login": login, "password": password}))
    if not token:
        die("v odpovědi na přihlášení nebyl nalezen token")
    print(f"::add-mask::{token}")  # pojistka: GitHub Actions token v logu zamaskuje

    query = urllib.parse.urlencode({"season": SEASON, "clubId": CLUB_ID})
    data = strip_contacts(request(f"{BASE}/team?{query}", token=token))

    # Pro každý tým stáhne soutěže z leagueGroups[].competitionId (každé ID se stahuje jen jednou)
    cache = {}
    for team in data.get("collection", []):
        ids = []
        for group in team.get("leagueGroups", []):
            cid = group.get("competitionId")
            if cid is not None and cid not in ids:
                ids.append(cid)
        competitions = []
        for cid in ids:
            if cid not in cache:
                cache[cid] = strip_contacts(
                    request(f"{BASE}/competition?{urllib.parse.urlencode({'competitionId': cid})}",
                            token=token))
            competitions.append(cache[cid])
        team["competitions"] = competitions

    new = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if OUT.exists() and OUT.read_text(encoding="utf-8") == new:
        print("Beze změny, nic se neukládá")
        return
    OUT.write_text(new, encoding="utf-8")
    print(f"Uloženo do {OUT.name}")


if __name__ == "__main__":
    main()



