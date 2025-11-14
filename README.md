# MTG RDF

A CLI tool to convert Magic: The Gathering card data from MTGJSON to RDF/Turtle format.

## Setup

```bash
uv sync
```

## Usage

**Full pipeline (extract + transform):**
```bash
uv run mtg-rdf --ingest
```

**Extract only (download MTGJSON data):**
```bash
uv run mtg-rdf --extract
```

**Transform only (convert to RDF/Turtle):**
```bash
uv run mtg-rdf --transform
```

**Help:**
```bash
uv run mtg-rdf --help
```

## Output

RDF graph in Turtle format using the [MTG Ontology](https://cmdoret.net/mtg_ontology/).
