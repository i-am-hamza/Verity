"""Cross-reference Reconcile Upload rows against source folder inventory."""
from dotenv import load_dotenv
load_dotenv(".env")

import hashlib
import re
import openpyxl
from pathlib import Path

from app.crawler import register_all_mappers
register_all_mappers()
from app.database import SessionLocal
from app.models.provenance import SourceDocument
from app.models.institution import Institution
from sqlalchemy import select

# Read source folder
source_dir = Path(r"E:\9. Verity\storage\reports")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# Build DB lookups
db = SessionLocal()
existing_docs = db.execute(select(SourceDocument)).scalars().all()
insts = db.execute(select(Institution).where(Institution.active == True)).scalars().all()
db.close()

existing_sha256 = {d.sha256: d for d in existing_docs}

# Name -> slug (from institution table)
# Build from DB names
INST_NAME_TO_SLUG = {i.name.lower(): i.slug for i in insts}
# Also add manual aliases
ALIASES = {
    "sabic agri-nutrients company": "saudi-arabian-fertilizer-company",
    "saudi basic industries corporation sabic": "sabic",
    "zain (mobile telecommunications company)": "zain-mobile-telecommunications-company",
    "mobile telecommunications co. saudi arabia (zain)": "mobile-telecommunications-co-saudi-arabia-zain",
    "aluminium bahrain (alba)": "aluminium-bahrain-alba",
    "ooredoo q.p.s.c.": "ooredoo-q-p-s-c",
    "qatar fuel company (woqod)": "qatar-fuel-company-woqod",
    "qatar gas transport co (nakilat)": "qatar-gas-transport-co-nakilat",
    "qnb (qatar national bank)": "qnb-qatar-national-bank",
    "rabigh refining & petrochemical co.": "rabigh-refining-petrochemical-co",
    "yanbu national petrochemical co": "yanbu-national-petrochemical",
    "the saudi national bank": "the-saudi-national-bank",
    "the national bank of ras al khaimah": "the-national-bank-of-ras-al-khaimah",
    "bahrain telecommunications beyon": "bahrain-telecommunications-beyon",
    "dubai investments pjsc": "dubai-investment",
    "gulf international services": "gulf-international-services",
    "saudi cement": "saudi-cement",
    "mouwasat medical services company": "mouwasat-medical-services-company",
    "national industrialization co": "national-industrialization-co",
    "bank albilad": "bank-albilad",
    "savola group": "savola-group",
    "oman international development and investment company": "oman-international-development-and-investment-company",
    "oman telecommunications company otel": "oman-telecommunications-company-otel",
    "sohar international bank": "sohar-international-bank",
    "tamdeen real estate company": "tamdeen-real-estate-company",
    "yanbu cement company": "yanbu-cement-company",
    "etihad etisalat (mobily)": "etihad-etisalat-mobily",
    "saudi airlines catering company catrion": "saudi-airlines-catering-company-catrion",
    "jarir marketing co": "jarir-marketing-co",
    "dar al arkan real estate development company": "dar-al-arkan-real-estate-development-company",
    "boubyan bank": "boubyan-bank",
    "air arabia pjsc": "air-arabia-pjsc",
    "advanced petrochemical": "advanced-petrochemical",
    "alinma bank": "alinma-bank",
    "aldar properties pjsc": "aldar-properties-pjsc",
    "kuwait telecommunications company": "kuwait-telecommunications-company",
    "industries qatar": "industries-qatar",
    "industries qatar": "industries-qatar",
    "first abu dhabi bank": "first-abu-dhabi-bank",
    "emirates nbd pjsc": "emirates-nbd-pjsc",
    "emirates telecom (etisalat group)": "emirates-telecom-etisalat-group",
    "saudi industrial investment group": "saudi-industrial-investment-group",
    "sabic agri-nutrients company": "saudi-arabian-fertilizer-company",
}
INST_NAME_TO_SLUG.update(ALIASES)


def company_to_slug(name):
    n = name.strip().lower()
    if n in INST_NAME_TO_SLUG:
        return INST_NAME_TO_SLUG[n]
    # Try partial match
    for key, slug in INST_NAME_TO_SLUG.items():
        if n in key or key in n:
            return slug
    return None


# Read Reconcile Upload rows
wb = openpyxl.load_workbook(r"E:\9. Verity\docs\methodology\Verity_Report_Status.xlsx",
                             read_only=True, data_only=True)
ws = wb["Reconcile"]
headers = None
upload_rows = []
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i == 0:
        headers = [str(c) if c is not None else f"col{i}" for i, c in enumerate(row)]
        continue
    if not row[0]:
        continue
    vals = dict(zip(headers, row))
    if vals.get("Action needed") == "Upload":
        upload_rows.append(vals)
wb.close()

# Build source folder inventory: (slug, year) -> [files]
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


from collections import defaultdict
source_files = defaultdict(list)  # (slug, year) -> [path, ...]

for pdf in sorted(source_dir.glob("*.pdf")):
    slug, year = guess_slug_year(pdf.name)
    if slug and year:
        source_files[(slug, year)].append(pdf)

# Cross-reference
print("=== CROSS-REFERENCE: Upload rows vs Source Folder ===\n")
print(f"{'Company':<55} {'FY':<6} {'Files found':<5} {'In DB?':<10}")
print("-" * 100)

found = 0
missing_count = 0
missing_rows = []

for r in upload_rows:
    company = r["Company"]
    fy_str = str(r["Fiscal year"])  # like 'FY2020'
    year_match = re.findall(r"\d{4}", fy_str)
    year = int(year_match[0]) if year_match else None
    slug = company_to_slug(company)

    files = source_files.get((slug, year), [])
    # Check if any file sha256 is in DB
    in_db_ids = []
    for f in files:
        sha = sha256_file(f)
        if sha in existing_sha256:
            in_db_ids.append(existing_sha256[sha].id)

    if files:
        found += 1
        in_db_str = f"YES({','.join(str(x) for x in in_db_ids)})" if in_db_ids else "no"
        note = r.get("Note") or ""
        print(f"{company:<55} {fy_str:<6} {len(files):<5} {in_db_str}  {note[:40] if note else ''}")
    else:
        missing_count += 1
        missing_rows.append(r)
        print(f"{company:<55} {fy_str:<6} MISSING (no file in source folder)")

print()
print(f"=== SUMMARY ===")
print(f"Upload rows with files: {found} / {len(upload_rows)}")
print(f"Upload rows MISSING files: {missing_count}")
print()
if missing_rows:
    print("=== MISSING COMPANY-YEARS (no file in source folder) ===")
    for r in missing_rows:
        note = r.get("Note") or ""
        print(f"  {r['Company']:<55} {r['Fiscal year']:<8} {note}")

# Also show duplicates that need resolution
print()
print("=== DUPLICATES IN SOURCE FOLDER (need decision on which to use) ===")
for (slug, year), files in sorted(source_files.items()):
    if len(files) > 1:
        print(f"  {slug} FY{year}:")
        for f in files:
            import pymupdf
            try:
                doc = pymupdf.open(str(f))
                pages = doc.page_count
                doc.close()
            except Exception:
                pages = "?"
            sha = sha256_file(f)
            in_db = sha in existing_sha256
            print(f"    {f.name:<60} {pages} pages  {'IN DB' if in_db else ''}")
