# Rozvrh tréninků TJ Sokol Vratimov

Stránka se rozvrhem tréninků a zápasy z eZapis.

## Struktura projektu

```
rozvrh-mladez/
├── index.html              # Hlavní stránka
├── logo.png                # Logo klubu
├── current.json            # Zápasy z eZapis (generuje se automaticky)
├── sitemap.xml             # Mapa webu pro SEO
├── robots.txt              # Pravidla pro roboty
├── _config.yml             # GitHub Pages config
└── scripts/
    └── fetch_current.py    # Script na stažení zápasů z eZapis
```

## Lokální testování `fetch_current.py`

### Instalace závislostí

Script nemá externí závislosti, používá jen standardní Python knihovny.

### Spuštění

Přejdi do adresáře projektu:

```bash
cd /Users/richard/Family/rozvrh-mladez
```

Spusť script:

```bash
python3 scripts/fetch_current.py
```

### Co se stane

- Script stáhne zápasy na dnešek a 8 dní dopředu (budoucí zápasy)
- Script stáhne zápasy z posledních 8 dní zpět (minulé zápasy)
- Filtruje zápasy, kde hraje "Sokol Vratimov"
- Uloží data do `current.json`
- Pro minulé zápasy se zobrazují jen dny se skutečnými zápasy
- Vypíše počet načtených budoucích a minulých zápasů

### Výstup

Příklad úspěšného běhu:
```
Uloženo 6 budoucích + 13 minulých zápasů
```

Pokud se nic nezmění:
```
Beze změny
```

Při chybě:
```
Chyba 2026-10-08: [popis chyby]
```

## Automatizace

Script je spouštěn automaticky prostřednictvím GitHub Actions každou hodinu (viz `.github/workflows/fetch.yml`).

## Data v `current.json`

```json
{
  "updated": "2026-10-12 12:44",
  "days": [
    {
      "date": "2026-10-12",
      "matches": []
    },
    {
      "date": "2026-10-14",
      "matches": [
        {
          "skupina": "OV-Z",
          "cislo": "(10)",
          "tymy": "TJ Hlučín - TJ Sokol Vratimov",
          "stav": "-",
          "badge": "",
          "href": "https://ezapis.cvf.cz/online/view.php?match=943013"
        }
      ]
    }
  ],
  "past_days": [
    {
      "date": "2026-10-11",
      "matches": [
        {
          "skupina": "MS-U16Z-T1D",
          "cislo": "(1)",
          "tymy": "TJ Sokol Vratimov \"A\" - TJ Frenštát p. R. \"B\"",
          "stav": "3:1 (23,-18,21,18)",
          "badge": "PLAY",
          "href": "https://ezapis.cvf.cz/online/view.php?match=953188"
        }
      ]
    }
  ]
}
```

### Pole v JSON

- **updated**: Čas poslední aktualizace
- **days**: Budoucí zápasy od dnešního dne až na 8 dní dopředu (včetně prázdných dní)
- **past_days**: Minulé zápasy z posledních 8 dní (jen dny se zápasy)

## Zobrazení na webu

Stránka `index.html`:
- Zobrazuje statický rozvrh tréninků
- Zobrazuje sekci **"Aktuální a budoucí zápasy"** (8 dní dopředu) - plánované zápasy od dnešího dne
  - Dnešní zápasy zobrazují řádek s výsledky a sety
  - Budoucí zápasy (ne dnešní) zobrazují jen týmy bez výsledků
- Zobrazuje sekci **"Odehrané zápasy - Minulý týden"** (8 dní zpět) - minulé zápasy od včerejška zpět
  - Zobrazují jen dny se skutečnými zápasy
  - Vždy zobrazují výsledky a jednotlivé sety
- Obě sekce dynamicky načítají data z `current.json`
- Dny bez zápasů se nezobrazují (v sekci aktuálních se dnešní den vždy zobrazí)
- Zápasy jsou seřazeny od nejnověji odehrané (minulé) a od dnešního dne (budoucí)

