"""Ingest class that orchestrates the extraction and transformation pipeline."""

import config
from extractor import Extractor
from transformer import Transformer


class Ingest:
    """Orchestrates the complete data ingestion pipeline from extraction to RDF transformation."""

    def __init__(self):
        """Initialize the ingest pipeline with extractor and transformer."""
        self.extractor = Extractor()
        self.transformer = Transformer()

    def run(self):
        """Execute the complete ingestion pipeline."""
        print("=" * 60)
        print("MTG RDF Ingestion Pipeline")
        print("=" * 60)

        # Step 1: Extract data from MTGJSON
        print("\n[1/2] Extracting data from MTGJSON...")
        self.extractor.extract()

        # Step 2: Transform to RDF
        print("\n[2/2] Transforming to RDF...")
        all_printings_path = config.ALL_PRINTINGS_FILEPATH

        if not all_printings_path.exists():
            print("Error: AllPrintings.json not found after extraction.")
            return False

        self.transformer.transform()

        print("\n" + "=" * 60)
        print("Ingestion complete!")
        print(f"RDF data saved to: {config.RDF_FILEPATH}")
        print("=" * 60)

        return True


if __name__ == "__main__":
    config.initialize()

    ingest = Ingest()
    success = ingest.run()

    exit(0 if success else 1)
