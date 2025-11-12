"""Configuration settings for the MTG RDF project."""

from pathlib import Path

META_URL = "https://mtgjson.com/api/v5/Meta.json"
ALL_PRINTINGS_URL = "https://mtgjson.com/api/v5/AllPrintings.json"
DATA_DIR = Path(__file__).parent.parent / "data"
RDF_FILEPATH = Path(f"{DATA_DIR}/mtg-rdf.ttl")
META_FILEPATH = Path(f"{DATA_DIR}/Meta.json")
ALL_PRINTINGS_FILEPATH = Path(f"{DATA_DIR}/AllPrintings.json")


def initialize():
    """Initialize the project environment by creating necessary directories."""
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)


