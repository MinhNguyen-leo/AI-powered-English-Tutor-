"""
Structured JSON logger for the AI English Tutor backend.
Logs every request/response to both console and a JSONL file.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "data"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "logs.jsonl"


class JSONLHandler(logging.Handler):
    """Appends each log record as a JSON line to a file."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
            }
            # Attach extra fields if present
            for key in ("user_id", "input", "context", "response"):
                if hasattr(record, key):
                    entry[key] = getattr(record, key)

            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            self.handleError(record)


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with console + JSONL file handlers."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Console handler (human-readable)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")
    )
    root.addHandler(console)

    # File handler (machine-readable JSONL)
    file_handler = JSONLHandler()
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(file_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
