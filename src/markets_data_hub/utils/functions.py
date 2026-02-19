"""Functions for scraping Riksbank auction data."""

import logging
import re
import time
import unicodedata
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.constants import KEY_MAP_GOV, KEY_MAP_RB_CERT

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = (10, 30)  # (connect, read) in seconds


def _create_session():
    """Create a requests session with retry logic and standard headers."""
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _parse_tables(page):
    """Extract list of dicts from all <table> elements on a page."""
    records = []
    tables = page.find_all("table")
    for tbl in tables:
        rec = {}
        for row in tbl.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                val = cells[1].get_text(strip=True)
                if key:
                    rec[key] = val
        if rec:
            records.append(rec)
    return records


### Riksbanks certificates


def is_auction_result_link(href):
    """Matches both new (auction results) and old (result-auction) URL patterns."""
    return "auktionsresultat-" in href or "result-auction-" in href


def scrape_rb_cert_auctions(limit=None, sleep_sec=0.5, from_date=None, to_date=None):
    """
    Web-scrapes the Riksbank's auction results for Riksbank certificates.
    Returns a LIST of dicts with raw text.
    """
    base_url = "https://www.riksbank.se"
    main_url = f"{base_url}/sv/marknader/marknadsoperationer/riksbankscertifikat/auctions-of-riksbank-certificates/"
    session = _create_session()

    resp = session.get(main_url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")

    year_urls = set()
    auction_links = []

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "/auctions-of-riksbank-certificates/" not in href:
            continue
        full_url = href if href.startswith("http") else base_url + href

        if is_auction_result_link(href):
            m = re.search(r"(\d{4}-\d{2}-\d{2})", href)
            if m:
                auction_links.append((m.group(1), full_url))
        elif re.search(r"/auctions-of-riksbank-certificates/\d{4}/?$", href):
            year_urls.add(full_url)

    for year_url in year_urls:
        try:
            r = session.get(year_url, timeout=REQUEST_TIMEOUT)
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
        except Exception as e:
            logger.warning("Failed to scrape year page %s: %s", year_url, e)
            continue

    links = sorted(set(auction_links), key=lambda x: x[0], reverse=True)

    if from_date:
        links = [(d, u) for d, u in links if d >= str(from_date)]
    if to_date:
        links = [(d, u) for d, u in links if d <= str(to_date)]
    if limit:
        links = links[:limit]

    records = []
    for i, (auction_date, url) in enumerate(links, 1):
        try:
            r = session.get(url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            page = BeautifulSoup(r.content, "html.parser")

            table_records = _parse_tables(page)
            if not table_records:
                records.append({"auction_date": auction_date, "source_url": url})
                continue

            page_text = page.get_text()
            isin_match = re.search(r"ISIN[:\s]*([A-Z]{2}\d{9,12})", page_text)

            for rec in table_records:
                rec["auction_date"] = auction_date
                rec["source_url"] = url
                if isin_match:
                    rec["ISIN"] = isin_match.group(1)
                records.append(rec)

            if sleep_sec:
                time.sleep(sleep_sec)

        except Exception as e:
            logger.warning("Failed to scrape auction %s: %s", url, e)
            records.append(
                {
                    "auction_date": auction_date,
                    "source_url": url,
                    "error": str(e),
                }
            )

    return records


def clean_key(key: str) -> str:
    """Normalize keys: remove diacritics, spaces, commas, special characters."""
    k = key.lower().strip()
    # ö → o, ä → a, å → a etc.
    k = unicodedata.normalize("NFD", k)
    k = "".join(c for c in k if unicodedata.category(c) != "Mn")
    k = re.sub(r"[,\.\s%]+", "_", k)
    k = re.sub(r"_+", "_", k)
    k = k.strip("_")
    return k


def clean_value(value, strip_bln=False):
    """Normalize a scraped value to int, float, date, or cleaned string.

    Args:
        value: The raw scraped value.
        strip_bln: If True, remove 'BLN'/'bln' unit markers (for certificate data).
    """
    if isinstance(value, str):
        v = value.strip()
        if v.lower() in ("n/a", "na", "-", ""):
            return None
        v = v.replace("\xa0", " ")
        if strip_bln:
            v = re.sub(r"\s*(BLN|bln)\s*", "", v)
        v = v.replace("%", "").strip()

        separators = [m.start() for m in re.finditer(r"[.,]", v)]
        if len(separators) >= 2:
            last = separators[-1]
            prefix = v[:last].replace(",", "").replace(".", "")
            suffix = v[last + 1 :]
            v = f"{prefix}.{suffix}"
        elif len(separators) == 1:
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
    """Clean both keys and values."""
    return {clean_key(k): clean_value(v, strip_bln=True) for k, v in raw.items()}


def transform_record(raw: dict) -> dict | None:
    normalized = normalize_record(raw)
    result = {}
    for norm_key, field_name in KEY_MAP_RB_CERT.items():
        if norm_key in normalized:
            result[field_name] = normalized[norm_key]

    required = {"Anbudsdag", "Rantesats", "Isin"}
    if not required.issubset(result.keys()):
        return None
    return result


### Sale of Government bonds


def scrape_riksbank_auctions(limit=None, sleep_sec=0.5, from_date=None, to_date=None):
    """
    Scrapes the Riksbank's auction pages and returns a LIST of dicts with raw text.
    Each dict corresponds to a found table on the respective page.
    """
    base_url = "https://www.riksbank.se"
    main_url = f"{base_url}/sv/marknader/marknadsoperationer/forsaljning-av-statsobligationer/auktionsresultat/"

    session = _create_session()

    resp = session.get(main_url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "/auktionsresultat/20" in href and href.endswith("/"):
            m = re.search(r"(\d{4}-\d{2}-\d{2})", href)
            if m:
                date = m.group(1)
                full_url = href if href.startswith("http") else base_url + href
                links.append((date, full_url))

    links = sorted(set(links), key=lambda x: x[0], reverse=True)
    if from_date:
        links = [(d, u) for d, u in links if d >= str(from_date)]
    if to_date:
        links = [(d, u) for d, u in links if d <= str(to_date)]
    if limit:
        links = links[:limit]

    records = []

    for i, (date, url) in enumerate(links, 1):
        try:
            r = session.get(url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            page = BeautifulSoup(r.content, "html.parser")

            table_records = _parse_tables(page)
            if not table_records:
                records.append({"auction_date": date, "source_url": url})
                continue

            for rec in table_records:
                rec["auction_date"] = date
                rec["source_url"] = url
                records.append(rec)

            if sleep_sec:
                time.sleep(sleep_sec)

        except Exception as e:
            logger.warning("Failed to scrape auction %s: %s", url, e)
            records.append(
                {
                    "auction_date": date,
                    "source_url": url,
                    "error": str(e),
                }
            )

    return records


def convert_record(row: dict):
    cleaned = {}
    for key, value in row.items():
        if key in KEY_MAP_GOV:
            new_key = KEY_MAP_GOV[key]
            cleaned[new_key] = clean_value(value)
    return cleaned
