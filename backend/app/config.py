"""
Application configuration.
Values are read from environment variables (see .env.example).
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Disclosure Scorer"
    environment: str = "development"

    # SQLite for the pilot phase — swap DATABASE_URL to a Postgres DSN
    # when moving past ~15-20 institutions / heavier concurrent processing.
    database_url: str = "sqlite:///./disclosure_scorer.db"

    storage_dir: Path = Path("storage/reports")

    # spaCy model used for sentence segmentation + lemma-based phrase matching
    spacy_model: str = "en_core_web_sm"

    # OCR is attempted only when native text extraction yields fewer than
    # this many characters per page (i.e. the page is likely a scanned image).
    ocr_trigger_char_threshold: int = 20

    # Tesseract executable + tessdata directory. Optional overrides for
    # non-standard installs (e.g. Windows + a user-writable tessdata folder).
    tesseract_cmd: str | None = None
    tessdata_prefix: Path | None = None
    ocr_langs: str = "eng+ara"

    # Matching mode:
    #   "longest": collapse overlapping matches to the longest span
    #              (avoids "corporate governance" also firing "governance").
    #   "all":     keep every match (documented as diagnostic-only).
    # Default here is a fallback — real value comes from config/verity.toml
    # via app.services.verity_config.load_verity_config().
    matching_mode: str = "longest"

    # Versions stamped onto every score row so old results stay traceable
    # after we change the taxonomy or the pipeline.
    taxonomy_version: str = "0.1.0"
    pipeline_version: str = "0.1.0"

    # Comma-separated list of origins allowed to call this API via CORS.
    # Session 10 deployment switch: on Render we set this to the Vercel
    # URL(s). Empty / unset means "no production origins configured" —
    # the dev-server fallback is applied in app.main so local tooling
    # (frontend Vite dev server on :5173) just works out of the box.
    allowed_origins: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def allowed_origin_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into a stripped, non-empty list; fall
        back to the Vite dev-server origin when nothing is configured so
        a local `uvicorn app.main:app` keeps working without extra env
        setup."""
        parts = [o.strip() for o in self.allowed_origins.split(",")]
        parts = [o for o in parts if o]
        return parts or ["http://localhost:5173"]


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
