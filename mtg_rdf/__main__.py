import argparse
from .extractor import Extractor
from .ingest import Ingest
from .transformer import Transformer

def main():
    parser = argparse.ArgumentParser(description='MTG RDF CLI')
    parser.add_argument('--ingest', action='store_true', help='run the ingest process')
    parser.add_argument('--extract', action='store_true', help='run the extract process')
    parser.add_argument('--transform', action='store_true', help='run the transform process')

    args = parser.parse_args()

    if args.ingest:
        i = Ingest()
        i.run()

    if args.extract:
        print("Running extract...")
        e = Extractor()
        e.extract()

    if args.transform:
        print("Running transform...")
        t = Transformer()
        t.transform()

    if not (args.ingest or args.extract or args.transform):
        parser.print_help()

if __name__ == "__main__":
    main()
