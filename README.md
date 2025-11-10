# MTG RDF

Convert Magic: The Gathering card data from MTGJSON to RDF/Turtle format.

## Setup

```bash
uv sync
```

## Usage

**Full pipeline (extract + transform):**
```bash
uv run python src/ingest.py
```

**Transform only (if you already have AllPrintings.json):**
```bash
uv run python src/transformer.py
```

## Output

RDF graph in Turtle format using the [MTG Ontology](https://cmdoret.net/mtg_ontology/).
