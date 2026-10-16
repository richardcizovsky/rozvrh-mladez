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


def request(url, data=None, token=None, soft=False):
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
        err = f"HTTP {e.code} při volání {url.split('?')[0]}"
    except Exception as e:
        err = f"{type(e).__name__} při volání {url.split('?')[0]}"
    if soft:
        print(f"Varování: {err}", file=sys.stderr)
        return None
    die(err)


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


# Klíče, ve kterých může být datum narození
BIRTH_RE = re.compile(r"(birth|narozen|dob$)", re.IGNORECASE)
# Další osobní údaje, které se u hráčů nikdy neukládají
PLAYER_DROP_RE = re.compile(
    r"(rodn|ssn|personal|passport|photo|foto|avatar|image|insurance|pojist|"
    r"citizen|obcan|idnp|^pid$|veto|^userId$|^gender$|^nationality$)",
    re.IGNORECASE,
)


def find_players(obj):
    """Najde seznam hráčů pod klíčem 'players' (kdekoli v odpovědi)."""
    if isinstance(obj, dict):
        if isinstance(obj.get("players"), list):
            return obj["players"]
        for v in obj.values():
            found = find_players(v)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = find_players(v)
            if found:
                return found
    return []


def birth_year_month(value):
    """Z data narození vrátí (rok, měsíc); den zahodí."""
    if not isinstance(value, str):
        return None
    m = re.match(r"\s*(\d{4})-(\d{1,2})", value) or None
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r"\s*\d{1,2}\.\s*(\d{1,2})\.\s*(\d{4})", value)
    if m:
        return int(m.group(2)), int(m.group(1))
    return None


def clean_player(player):
    """Zahodí kontakty a osobní údaje; datum narození nahradí birthYear a birthMonth."""
    if not isinstance(player, dict):
        return {}
    out = {}
    for k, v in player.items():
        if BIRTH_RE.search(k):
            ym = birth_year_month(v)
            if ym:
                out["birthYear"], out["birthMonth"] = ym
        elif not CONTACT_RE.search(k) and not PLAYER_DROP_RE.search(k):
            out[k] = strip_contacts(v)
    return out


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
    group_cache = {}
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

        # Soupiska: jen hráči, z data narození zůstane pouze rok a měsíc
        roster = request(f"{BASE}/team/{team['id']}/with-roster", token=token)
        team["players"] = [clean_player(p) for p in find_players(roster)]

        # Tabulka a rozpis zápasů každé skupiny (každé groupId se stahuje jen jednou)
        for group in team.get("leagueGroups", []):
            gid = group.get("groupId")
            if gid is None:
                continue
            if gid not in group_cache:
                sb = request(f"{BASE}/group/{gid}/scoreboard", token=token, soft=True)
                sc = request(f"{BASE}/match/{gid}/schedule", token=token, soft=True)
                group_cache[gid] = {
                    "scoreboard": strip_contacts(sb) if sb is not None else None,
                    "schedule": strip_contacts(sc) if sc is not None else None,
                }
            group.update(group_cache[gid])

    new = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if OUT.exists() and OUT.read_text(encoding="utf-8") == new:
        print("Beze změny, nic se neukládá")
        return
    OUT.write_text(new, encoding="utf-8")
    print(f"Uloženo do {OUT.name}")


if __name__ == "__main__":
    main()



