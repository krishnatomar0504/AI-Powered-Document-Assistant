import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR") or PROJECT_ROOT).expanduser()
if not DATA_DIR.is_absolute():
    DATA_DIR = PROJECT_ROOT / DATA_DIR
DATA_DIR = DATA_DIR.resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

PDF_DIR = (
    DATA_DIR / "pdf"
    if os.getenv("DATA_DIR")
    else PROJECT_ROOT / "data" / "pdf"
)
PDF_DIR.mkdir(parents=True, exist_ok=True)
