"""Functions."""

import re
import time
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import unicodedata

from utils.constants import KEY_MAP

def is_auction_result_link(href):
    """Matchar både nya (auktionsresultat-) och gamla (result-auction-) URL-mönster."""
    return "auktionsresultat-" in href or "result-auction-" in href


def scrape_rb_cert_auctions(limit=None, sleep_sec=0.5, from_date=None, to_date=None):
    """
    Skrapar Riksbankens auktionsresultat för riksbankscertifikat.
    Returnerar en LISTA av dicts med råtext.
    """
    base_url = "https://www.riksbank.se"
    main_url = f"{base_url}/sv/marknader/marknadsoperationer/riksbankscertifikat/auctions-of-riksbank-certificates/"
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )

    resp = session.get(main_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")

    # Steg 1: Hitta alla årssidor + eventuella direktlänkar
    year_urls = set()
    auction_links = []

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "/auctions-of-riksbank-certificates/" not in href:
            continue
        full_url = href if href.startswith("http") else base_url + href

        # Direktlänk till auktionsresultat
        if is_auction_result_link(href):
            m = re.search(r"(\d{4}-\d{2}-\d{2})", href)
            if m:
                auction_links.append((m.group(1), full_url))
        # Årssida, t.ex. .../2018/, .../2019/
        elif re.search(r"/auctions-of-riksbank-certificates/\d{4}/?$", href):
            year_urls.add(full_url)

    # Steg 2: Besök varje årssida och hämta auktionslänkar
    for year_url in year_urls:
        try:
            r = session.get(year_url)
            r.raise_for_status()
            year_soup = BeautifulSoup(r.content, "html.parser")
            for a in year_soup.find_all("a", href=True):
                href = a.get("href", "")
                if is_auction_result_link(href):
                    m = re.search(r"(\d{4}-\d{2}-\d{2})", href)
                    if m:
                        full = href if href.startswith("http") else base_url + href
                        auction_links.append((m.group(1), full))
            if sleep_sec:
                time.sleep(sleep_sec)
        except Exception:
            continue

    # Dedup och sortera
    links = sorted(set(auction_links), key=lambda x: x[0], reverse=True)

    if from_date:
        links = [(d, u) for d, u in links if d >= str(from_date)]
    if to_date:
        links = [(d, u) for d, u in links if d <= str(to_date)]
    if limit:
        links = links[:limit]

    # Steg 3: Skrapa varje auktionssida
    records = []
    for i, (auction_date, url) in enumerate(links, 1):
        try:
            r = session.get(url)
            r.raise_for_status()
            page = BeautifulSoup(r.content, "html.parser")
            tables = page.find_all("table")

            if not tables:
                records.append({"auction_date": auction_date, "source_url": url})
                continue

            for tbl in tables:
                rec = {"auction_date": auction_date, "source_url": url}
                for row in tbl.find_all("tr"):
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        val = cells[1].get_text(strip=True)
                        if key:
                            rec[key] = val
                if len(rec) > 2:
                    records.append(rec)

            # ISIN: ligger som fritext under tabellen
            page_text = page.get_text()
            isin_match = re.search(r"ISIN[:\s]*([A-Z]{2}\d{9,12})", page_text)
            if isin_match:
                for rec in records:
                    if rec.get("source_url") == url:
                        rec["ISIN"] = isin_match.group(1)

            if sleep_sec:
                time.sleep(sleep_sec)

        except Exception as e:
            records.append(
                {
                    "auction_date": auction_date,
                    "source_url": url,
                    "error": str(e),
                }
            )

    return records


def clean_key(key: str) -> str:
    """Normalisera nycklar: ta bort diakritiska tecken, mellanslag, komma, specialtecken."""
    k = key.lower().strip()
    # ö → o, ä → a, å → a etc.
    k = unicodedata.normalize("NFD", k)
    k = "".join(c for c in k if unicodedata.category(c) != "Mn")
    k = re.sub(r"[,\.\s%]+", "_", k)
    k = re.sub(r"_+", "_", k)
    k = k.strip("_")
    return k


def clean_value(value):
    if isinstance(value, str):
        v = value.strip()
        if v.lower() in ("n/a", "na", "-", ""):
            return None
        v = v.replace("\xa0", " ")
        v = re.sub(r"\s*(BLN|bln)\s*", "", v)
        v = v.replace("%", "").strip()

        # Hantera tusentalsavgränsare:
        # "1.293.700" eller "1,278.700" → behåll bara sista punkten som decimal
        # Strategi: om det finns flera punkter/komma, ta bort alla utom den sista
        separators = [m.start() for m in re.finditer(r"[.,]", v)]
        if len(separators) >= 2:
            # Flera separatorer → allt utom sista är tusentalsavgränsare
            last = separators[-1]
            prefix = v[:last].replace(",", "").replace(".", "")
            suffix = v[last + 1:]
            v = f"{prefix}.{suffix}"
        elif len(separators) == 1:
            # En separator → kolla om det är komma (svenskt decimal) eller punkt
            v = v.replace(",", ".")

        v = v.replace(" ", "")

        if re.fullmatch(r"-?\d+", v):
            return int(v)
        if re.fullmatch(r"-?\d+\.\d+", v):
            return float(v)
        for fmt in ("%Y-%m-%d",):
            try:
                return datetime.strptime(v, fmt).date()
            except ValueError:
                pass
    return value


def normalize_record(raw: dict) -> dict:
    """Rensa både nycklar och värden."""
    return {clean_key(k): clean_value(v) for k, v in raw.items()}


def transform_record(raw: dict) -> dict | None:
    normalized = normalize_record(raw)
    result = {}
    for norm_key, field_name in KEY_MAP.items():
        if norm_key in normalized:
            result[field_name] = normalized[norm_key]
    
    # Kräv minst dessa fält för att vara en giltig post
    required = {"Anbudsdag", "Rantesats", "Isin"}
    if not required.issubset(result.keys()):
        return None
    return result
