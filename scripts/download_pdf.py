# -*- coding: utf-8 -*-
"""Download an open-access PDF for a DOI, PMID, or direct URL.

This is the self-contained fallback for the parameter-evidence workflow. It
never bypasses a paywall or login. It asks OpenAlex, Unpaywall, and Europe PMC
for an explicitly open PDF, verifies the PDF signature, and writes the file.

Usage:
    python download_pdf.py 10.1371/journal.pcbi.1000771 --out-dir pdfs --email you@example.org
    python download_pdf.py 15966900 --out-dir pdfs
    python download_pdf.py https://example.org/paper.pdf --out-dir pdfs --filename paper.pdf

Exit codes:
    0  PDF downloaded
    2  no authorized open-access PDF found
    3  input not recognized
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = {
    "User-Agent": "parameter-evidence-support/1.0 (mailto:research@example.org)",
    "Accept": "application/pdf,application/json,text/html;q=0.8,*/*;q=0.5",
}


def get_json(url, timeout=45, tries=3):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except Exception as exc:
            last = exc
            if attempt + 1 < tries:
                time.sleep(1.0 * (attempt + 1))
    print(f"[warn] request failed: {url} -> {last}", file=sys.stderr)
    return {}


def clean_doi(value):
    value = value.strip()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.I)
    value = re.sub(r"^doi:\s*", "", value, flags=re.I)
    return value


def clean_pmid(value):
    value = value.strip()
    value = re.sub(r"^pmid:\s*", "", value, flags=re.I)
    return value if value.isdigit() else ""


def safe_name(value, fallback="paper", max_length=110):
    value = re.sub(r"[^\w\-. ]+", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "_", value).strip("._- ")
    return (value[:max_length] or fallback)


def add_url(rows, url, source):
    if not url:
        return
    url = str(url).strip()
    if not url.lower().startswith(("http://", "https://")):
        return
    for row in rows:
        if row["url"] == url:
            return
    rows.append({"url": url, "source": source})


def crossref_metadata(doi):
    data = get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe=""))
    message = data.get("message", {}) if isinstance(data, dict) else {}
    authors = []
    for author in message.get("author", []) or []:
        family = author.get("family") or ""
        given = author.get("given") or ""
        if family:
            authors.append((family + " " + given).strip())
    title = (message.get("title") or [""])[0]
    year = ((message.get("issued", {}).get("date-parts") or [[None]])[0] or [None])[0]
    return {
        "title": title,
        "authors": authors,
        "year": year,
        "journal": (message.get("container-title") or [""])[0],
    }


def openalex_candidates(doi):
    work = get_json("https://api.openalex.org/works/https://doi.org/" + urllib.parse.quote(doi, safe=""))
    rows = []
    if not isinstance(work, dict):
        return rows, {}
    for key in ("best_oa_location", "primary_location"):
        location = work.get(key) or {}
        if isinstance(location, dict):
            add_url(rows, location.get("pdf_url"), "OpenAlex " + key)
    for location in work.get("locations", []) or []:
        if isinstance(location, dict):
            add_url(rows, location.get("pdf_url"), "OpenAlex location")
    authors = []
    for authorship in work.get("authorships", []) or []:
        name = ((authorship.get("author") or {}).get("display_name") or "")
        if name:
            authors.append(name)
    metadata = {
        "title": work.get("display_name") or work.get("title") or "",
        "authors": authors,
        "year": work.get("publication_year"),
        "journal": ((work.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
    }
    return rows, metadata


def unpaywall_candidates(doi, email):
    if not email:
        return []
    data = get_json(
        "https://api.unpaywall.org/v2/"
        + urllib.parse.quote(doi, safe="")
        + "?email="
        + urllib.parse.quote(email)
    )
    rows = []
    if not isinstance(data, dict):
        return rows
    for key in ("best_oa_location",):
        location = data.get(key) or {}
        if isinstance(location, dict):
            add_url(rows, location.get("url_for_pdf"), "Unpaywall " + key)
            add_url(rows, location.get("url"), "Unpaywall " + key + " landing URL")
    for location in data.get("oa_locations", []) or []:
        if isinstance(location, dict):
            add_url(rows, location.get("url_for_pdf"), "Unpaywall OA location")
    return rows


def europepmc_record(identifier, kind):
    if kind == "doi":
        query = f'DOI:"{identifier}"'
    else:
        query = f'EXT_ID:{identifier} AND SRC:MED'
    params = {
        "query": query,
        "format": "json",
        "resultType": "core",
        "pageSize": "3",
    }
    data = get_json(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
        + urllib.parse.urlencode(params)
    )
    results = ((data.get("resultList") or {}).get("result") or []) if isinstance(data, dict) else []
    return results[0] if results else {}


def europepmc_candidates(identifier, kind):
    record = europepmc_record(identifier, kind)
    rows = []
    if not record:
        return rows, {}
    for item in ((record.get("fullTextUrlList") or {}).get("fullTextUrl") or []):
        if not isinstance(item, dict):
            continue
        url = item.get("url") or ""
        style = (item.get("documentStyle") or "").lower()
        if style == "pdf" or ".pdf" in url.lower():
            add_url(rows, url, "Europe PMC fullTextUrlList")
    pmcid = record.get("pmcid") or ""
    if pmcid:
        add_url(rows, f"https://europepmc.org/articles/{pmcid}?pdf=render", "Europe PMC render")
        add_url(rows, f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/", "PMC OA")
    metadata = {
        "title": record.get("title", ""),
        "authors": [x.strip() for x in (record.get("authorString") or "").split(",") if x.strip()],
        "year": record.get("pubYear", ""),
        "journal": ((record.get("journalInfo") or {}).get("journal") or {}).get("title", ""),
        "pmcid": pmcid,
        "pmid": record.get("pmid", ""),
        "doi": record.get("doi", ""),
    }
    return rows, metadata


def try_download(url, destination):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            head = response.read(8)
            if b"%PDF-" not in head:
                return False, "response is not a PDF"
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as handle:
                handle.write(head)
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
            if destination.stat().st_size < 1000:
                destination.unlink(missing_ok=True)
                return False, "downloaded file is too small"
            return True, str(destination)
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except Exception as exc:
        return False, str(exc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("identifier", help="DOI, PMID, or direct PDF URL")
    parser.add_argument("--out-dir", default="pdfs", help="destination directory")
    parser.add_argument("--email", default="", help="email for Unpaywall API (optional)")
    parser.add_argument("--filename", default="", help="output filename, without or with .pdf")
    parser.add_argument("--dry-run", action="store_true", help="list candidate URLs without downloading")
    args = parser.parse_args()

    identifier = args.identifier.strip()
    kind = ""
    doi = ""
    pmid = ""
    rows = []
    metadata = {}

    if re.match(r"^https?://", identifier, flags=re.I):
        kind = "url"
        add_url(rows, identifier, "direct URL")
        metadata = {"title": Path(urllib.parse.urlparse(identifier).path).stem}
    elif clean_doi(identifier).lower().startswith("10."):
        kind = "doi"
        doi = clean_doi(identifier)
        metadata = crossref_metadata(doi)
        openalex_rows, openalex_meta = openalex_candidates(doi)
        rows.extend(openalex_rows)
        metadata = {**openalex_meta, **{k: v for k, v in metadata.items() if v}}
        rows.extend(unpaywall_candidates(doi, args.email))
        epmc_rows, epmc_meta = europepmc_candidates(doi, "doi")
        rows.extend(epmc_rows)
        metadata = {**epmc_meta, **{k: v for k, v in metadata.items() if v}}
    elif clean_pmid(identifier):
        kind = "pmid"
        pmid = clean_pmid(identifier)
        epmc_rows, epmc_meta = europepmc_candidates(pmid, "pmid")
        rows.extend(epmc_rows)
        metadata = epmc_meta
        if epmc_meta.get("doi") and not doi:
            doi = epmc_meta["doi"]
            meta2 = crossref_metadata(doi)
            metadata = {**metadata, **{k: v for k, v in meta2.items() if v}}
    else:
        print("Unrecognized identifier. Provide a DOI, a numeric PMID, or an http(s) PDF URL.", file=sys.stderr)
        return 3

    # De-duplicate while preserving priority: OpenAlex, Unpaywall, Europe PMC, direct URL.
    unique = []
    seen = set()
    for row in rows:
        if row["url"] not in seen:
            seen.add(row["url"])
            unique.append(row)
    rows = unique

    print(f"identifier={identifier} kind={kind} candidates={len(rows)}")
    for index, row in enumerate(rows, 1):
        print(f"  {index}. [{row['source']}] {row['url']}")

    if not rows:
        print("【找不到开放获取 PDF】No open-access PDF URL was returned. Use the publisher page, an authorized institutional session, or supply a local PDF manually.", file=sys.stderr)
        return 2
    if args.dry_run:
        return 0

    if args.filename:
        filename = args.filename if args.filename.lower().endswith(".pdf") else args.filename + ".pdf"
        filename = safe_name(Path(filename).stem) + ".pdf"
    else:
        first_author = (metadata.get("authors") or ["paper"])[0].split()[0]
        year = metadata.get("year") or "unknown"
        title = metadata.get("title") or (doi or pmid or "paper")
        filename = f"{safe_name(str(first_author), 'paper')}_{year}_{safe_name(str(title), 'paper', 70)}.pdf"
    destination = Path(args.out_dir) / filename

    errors = []
    for row in rows:
        ok, message = try_download(row["url"], destination)
        if ok:
            print("downloaded=" + str(destination))
            print(json.dumps({"file": str(destination), "source": row["source"], "url": row["url"], "metadata": metadata}, ensure_ascii=False, indent=2))
            return 0
        errors.append({"url": row["url"], "source": row["source"], "error": message})
        print(f"[skip] {row['source']}: {message}", file=sys.stderr)

    print("【找不到可用 PDF】All candidate URLs failed; no paywall bypass was attempted.", file=sys.stderr)
    print(json.dumps({"errors": errors}, ensure_ascii=False, indent=2), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())