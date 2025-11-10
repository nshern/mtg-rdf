import requests
import config
from config import META_URL, ALL_PRINTINGS_URL, DATA_DIR, RDF_FILEPATH, META_FILEPATH, ALL_PRINTINGS_FILEPATH
import json


config.initialize()

class Extractor():
    """Extractor class for fetching MTG JSON data."""

    def __init__(self):
        self.meta_url = META_URL
        self.all_printings_url = ALL_PRINTINGS_URL
        self.data_dir = DATA_DIR

    def __fetch_data(self, url):
        """Fetch JSON data from a given URL."""
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def extract(self):
        """Extract MTG JSON data."""

        extraction_required = False

        if not RDF_FILEPATH.exists() or not META_FILEPATH.exists():
            extraction_required = True

        if META_FILEPATH.exists():
            with open(META_FILEPATH, 'r', encoding='utf-8') as f:
                local_meta_data = json.load(f)
            meta_data = self.__fetch_data(self.meta_url)
            data_date = meta_data['data']['date']
            if local_meta_data['data']['date'] != data_date:
                extraction_required = True

        if extraction_required:
            print("Extraction required. Fetching data...")
            meta_data = self.__fetch_data(self.meta_url)
            with open(META_FILEPATH, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=4)
            print("Meta data updated.")

            print("Downloading...")
            all_printings = self.__fetch_data(self.all_printings_url)
            with open(ALL_PRINTINGS_FILEPATH, 'w', encoding='utf-8') as f:
                json.dump(all_printings, f, ensure_ascii=False, indent=4)
            print("Done!")

if __name__ == "__main__":
    extractor = Extractor()
    extractor.extract()




