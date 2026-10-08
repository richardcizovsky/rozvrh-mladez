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

- Script stáhne zápasy na dnešek a 7 dní dopředu
- Filtruje zápasy, kde hraje "Sokol Vratimov"
- Uloží data do `current.json`
- Vypíše počet načtených zápasů

### Výstup

Příklad úspěšného běhu:
```
Uloženo 8 zápasů (2026-10-08 – 2026-10-16)
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
  "updated": "2026-10-08 08:34",
  "days": [
    {
      "date": "2026-10-08",
      "matches": [
        {
          "skupina": "MS-U18ZA",
          "cislo": "(20)",
          "tymy": "TJ Sokol Vratimov - TJ Odry",
          "stav": "-",
          "badge": "PLAY",
          "href": "https://ezapis.cvf.cz/online/view.php?match=936548"
        }
      ]
    }
  ]
}
```

## Zobrazení na webu

Stránka `index.html`:
- Zobrazuje statický rozvrh tréninků
- Pod tím dynamicky načítá zápasy z `current.json`
- Dnešní zápasy zobrazuje s výsledky a časy
- Budoucí zápasy zobrazuje bez výsledků
- Dny bez zápasů se nezobrazují (jen dnešní den se vždy zobrazí)

