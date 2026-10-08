"""Inventory script: list all PDFs in source folder with sha256, page count, and DB match."""
from dotenv import load_dotenv
load_dotenv('.env')

import hashlib
import re
from pathlib import Path
import pymupdf

from app.crawler import register_all_mappers
register_all_mappers()
from app.database import SessionLocal
from app.models.provenance import SourceDocument
from sqlalchemy import select

# Build sha256 -> source_doc map from DB
db = SessionLocal()
existing_docs = db.execute(select(SourceDocument)).scalars().all()
existing_sha256 = {d.sha256: d for d in existing_docs}
db.close()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def page_count(path):
    try:
        doc = pymupdf.open(str(path))
        n = doc.page_count
        doc.close()
        return n
    except Exception as e:
        return f"ERR:{e}"


# Name -> slug mapping
NAME_TO_SLUG = {
    "abdullah al othaim": "abdullah-al-othaim-markets",
    "abu dhabi commercial bank": "abu-dhabi-commercial-bank",
    "abu dhabi national energy": "abu-dhabi-national-energy-company",
    "abu dhabi national oil": "abu-dhabi-national-oil-company-for-distribution",
    "advanced petrochemical": "advanced-petrochemical",
    "air arabia": "air-arabia-pjsc",
    "al rajhi": "al-rajhi-bank",
    "aldar properties": "aldar-properties-pjsc",
    "alinma bank": "alinma-bank",
    "almarai": "almarai",
    "aluminium bahrain": "aluminium-bahrain-alba",
    "bahrain telecommunications": "bahrain-telecommunications-beyon",
    "baladna": "baladna",
    "bank al bilad": "bank-albilad",
    "bank albilad": "bank-albilad",
    "bank dhofar": "bank-dhofar",
    "bank muscat": "bank-muscat-bkmb",
    "barwa real estate": "barwa-real-estate",
    "boubyan bank": "boubyan-bank",
    "dar al arkan": "dar-al-arkan-real-estate-development-company",
    "dubai investments": "dubai-investment",
    "dubai islamic bank": "dubai-islamic-bank",
    "emirates nbd": "emirates-nbd-pjsc",
    "emirates telecom": "emirates-telecom-etisalat-group",
    "etihad etisalat": "etihad-etisalat-mobily",
    "first abu dhabi bank": "first-abu-dhabi-bank",
    "gulf hotels group": "gulf-hotels-group",
    "gulf international services": "gulf-international-services",
    "industries qatar": "industries-qatar",
    "jarir marketing": "jarir-marketing-co",
    "jazeera airways": "jazeera-airways",
    "jazeera steel": "jazeera-steel",
    "kuwait finance house": "kuwait-finance-house",
    "kuwait telecommunications": "kuwait-telecommunications-company",
    "maa_den": "maaden",
    "ma_aden": "maaden",
    "mobile telecommunications co annual": "mobile-telecommunications-co-saudi-arabia-zain",
    "mouwasat medical": "mouwasat-medical-services-company",
    "national bank of bahrain": "national-bank-of-bahrain",
    "national bank of kuwait": "national-bank-of-kuwait",
    "national industrialization": "national-industrialization-co",
    "oman international development": "oman-international-development-and-investment-company",
    "oman telecommunications": "oman-telecommunications-company-otel",
    "ooredoo": "ooredoo-q-p-s-c",
    "qatar fuel": "qatar-fuel-company-woqod",
    "qatar gas transport": "qatar-gas-transport-co-nakilat",
    "qnb": "qnb-qatar-national-bank",
    "rabigh refining": "rabigh-refining-petrochemical-co",
    "riyadh bank": "riyad-bank",
    "riyad bank": "riyad-bank",
    "sahara international petrochemical": "sahara-international-petrochemical-co",
    "salam international": "salam-international-investment",
    "saudi airlines catering": "saudi-airlines-catering-company-catrion",
    "saudi aramco": "saudi-aramco",
    "saudi cement": "saudi-cement",
    "saudi industrial investment": "saudi-industrial-investment-group",
    "saudi national bank": "the-saudi-national-bank",
    "savola": "savola-group",
    "sohar international": "sohar-international-bank",
    "tamdeen real estate": "tamdeen-real-estate-company",
    "the national bank of ras al khaimah": "the-national-bank-of-ras-al-khaimah",
    "yanbu cement": "yanbu-cement-company",
    "yanbu national petrochemical": "yanbu-national-petrochemical",
    "zain - mobile": "zain-mobile-telecommunications-company",
    "sabic integrated": "sabic",
    "sabic_annual": "sabic",
    "sabic annual": "sabic",
    "maaden annual": "maaden",
    "ncb": "the-saudi-national-bank",
}

# Special per-filename overrides (for ambiguous cases)
FILENAME_OVERRIDES = {
    "NCB (SNB) -Annual-Report-2020.pdf": ("the-saudi-national-bank", 2020),
    "saudi-aramco-ara-2020-english.pdf": ("saudi-aramco", 2020),
    "saudi-aramco-ara-2021-english.pdf": ("saudi-aramco", 2021),
    "saudi-aramco-ara-2022-english.pdf": ("saudi-aramco", 2022),
    "saudi-aramco-ara-2024-english.pdf": ("saudi-aramco", 2024),
    "saudi-aramco-ara-2025-english.pdf": ("saudi-aramco", 2025),
    "SABIC-Integrated-Annual-Report-2023.pdf": ("sabic", 2023),
    "SABIC-Integrated-Annual-Report-2024.pdf": ("sabic", 2024),
    "SABIC_Annual_Report_2021.pdf": ("sabic", 2021),
    "Maa_den Annual Report 2020.pdf": ("maaden", 2020),
    "ma_aden-annual-report-2021.pdf": ("maaden", 2021),
    "STC Annual-Report 2020.pdf": ("saudi-telecom-company", 2020),
    "STC-Annual-Report-2021.pdf": ("saudi-telecom-company", 2021),
    "stc-annual-report-2022.pdf": ("saudi-telecom-company", 2022),
    "stc-annual-report-2023.pdf": ("saudi-telecom-company", 2023),
    "stc_Annual Report-2024.pdf": ("saudi-telecom-company", 2024),
    "Stc-Anuual-Report-2025.pdf": ("saudi-telecom-company", 2025),
    "Saudi National Bank 2022.pdf": ("the-saudi-national-bank", 2022),
    "Mobile Telecommunications Co Annual Report 2020.pdf": ("mobile-telecommunications-co-saudi-arabia-zain", 2020),
    "Mobile Telecommunications Co Annual Report 2021.pdf": ("mobile-telecommunications-co-saudi-arabia-zain", 2021),
    "Mobile Telecommunications Co Annual Report 2022.pdf": ("mobile-telecommunications-co-saudi-arabia-zain", 2022),
    "Mobile Telecommunications Co Annual Report 2023.pdf": ("mobile-telecommunications-co-saudi-arabia-zain", 2023),
    "Mobile Telecommunications Co Annual Report 2024.pdf": ("mobile-telecommunications-co-saudi-arabia-zain", 2024),
    "Mobile Telecommunications Co Annual Report 2025.pdf": ("mobile-telecommunications-co-saudi-arabia-zain", 2025),
    "Zain - Mobile Telecommunications Co - Annual Report 2020.pdf": ("zain-mobile-telecommunications-company", 2020),
    "Zain - Mobile Telecommunications Co - Annual Report 2021.pdf": ("zain-mobile-telecommunications-company", 2021),
    "Zain - Mobile Telecommunications Co - Annual Report 2022.pdf": ("zain-mobile-telecommunications-company", 2022),
    "Zain - Mobile Telecommunications Co - Annual Report 2023.pdf": ("zain-mobile-telecommunications-company", 2023),
    "Zain - Mobile Telecommunications Co - Annual Report 2025.pdf": ("zain-mobile-telecommunications-company", 2025),
}


def guess_slug_year(fname):
    if fname in FILENAME_OVERRIDES:
        return FILENAME_OVERRIDES[fname]
    fname_lower = fname.lower()
    slug = None
    for key, s in NAME_TO_SLUG.items():
        if key.lower() in fname_lower:
            slug = s
            break
    years = re.findall(r"\b(202[0-5])\b", fname)
    year = int(years[0]) if years else None
    return slug, year


source_dir = Path(r"E:\9. Verity\storage\reports")
pdfs = sorted(source_dir.glob("*.pdf"))
print(f"Total PDFs in source folder: {len(pdfs)}")
print()

results = []
unmatched = []
for pdf in pdfs:
    fname = pdf.name
    slug, year = guess_slug_year(fname)
    sha = sha256_file(pdf)
    pages = page_count(pdf)

    in_db = sha in existing_sha256
    db_doc = existing_sha256.get(sha)
    db_id = db_doc.id if db_doc else None

    results.append({
        "fname": fname,
        "slug": slug,
        "year": year,
        "sha256": sha,
        "pages": pages,
        "in_db": in_db,
        "db_id": db_id,
    })

    if not slug or not year:
        unmatched.append({"fname": fname, "slug": slug, "year": year})

# Print full inventory
print(f"{'File':<70} {'Slug':<52} {'FY':<6} {'Pages':<7} {'In DB'}")
print("-" * 160)
for r in results:
    slug_str = r["slug"] or "UNMATCHED"
    yr_str = str(r["year"]) if r["year"] else "???"
    in_db_str = f"YES(id={r['db_id']})" if r["in_db"] else "no"
    print(f"{r['fname']:<70} {slug_str:<52} {yr_str:<6} {str(r['pages']):<7} {in_db_str}")

print()
print(f"=== UNMATCHED ({len(unmatched)} files) ===")
for u in unmatched:
    print(f"  {u['fname']}  slug={u['slug']}  year={u['year']}")

print()
print(f"=== SUMMARY ===")
print(f"Total files: {len(results)}")
matched = [r for r in results if r["slug"] and r["year"]]
print(f"Matched: {len(matched)}")
print(f"Unmatched: {len(unmatched)}")
print(f"Already in DB: {sum(1 for r in results if r['in_db'])}")
print(f"Not in DB (new): {sum(1 for r in results if not r['in_db'])}")

# Check for duplicate company-years
from collections import Counter
cy_counter = Counter((r["slug"], r["year"]) for r in matched)
dupes = {k: v for k, v in cy_counter.items() if v > 1}
if dupes:
    print(f"\nDUPLICATE (slug, year) in source folder:")
    for k, v in dupes.items():
        print(f"  {k[0]} FY{k[1]}: {v} files")
