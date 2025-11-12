"""Transformer class for converting MTG JSON data to RDF."""

from .config import ALL_PRINTINGS_FILEPATH, RDF_FILEPATH
import json
from rdflib import Graph, Namespace, Literal, URIRef, RDF, XSD
from tqdm import tqdm


# Define MTG ontology namespace
MTGO = Namespace("https://cmdoret.net/mtg_ontology/")


class Transformer:
    def __init__(self):
        self.graph = Graph()
        self.graph.bind("mtgo", MTGO)
        self._data = None

    @property
    def data(self):
        """Lazy load the JSON data on first access."""
        if self._data is None:
            with open(ALL_PRINTINGS_FILEPATH, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        return self._data

    def add_card(self, card_info, set_name):
        card_uri = URIRef(MTGO + f"card/{card_info['uuid']}")

        # Valid card type classes defined in the MTG ontology
        VALID_TYPES = {
            "Artifact",
            "Creature",
            "Enchantment",
            "Instant",
            "Land",
            "Sorcery",
        }

        # Always add base Card type (explicit is better than implicit)
        self.graph.add((card_uri, RDF.type, MTGO.Card))

        # Also add specific type classes (Land, Creature, Artifact, etc.)
        if "types" in card_info:
            for card_type in card_info["types"]:
                # Only add if it's a valid ontology class
                if card_type in VALID_TYPES:
                    type_class = MTGO[card_type]
                    self.graph.add((card_uri, RDF.type, type_class))

        # Basic card info
        if "name" in card_info:
            self.graph.add((card_uri, MTGO.name, Literal(card_info["name"])))

        if "artist" in card_info:
            self.graph.add((card_uri, MTGO.artist, Literal(card_info["artist"])))

        if "uuid" in card_info:
            self.graph.add((card_uri, MTGO.id, Literal(card_info["uuid"])))

        # Card types
        if "type" in card_info:
            self.graph.add((card_uri, MTGO.card_type, Literal(card_info["type"])))

        if "types" in card_info:
            for card_type in card_info["types"]:
                self.graph.add((card_uri, MTGO.card_type, Literal(card_type)))

        if "subtypes" in card_info:
            for subtype in card_info["subtypes"]:
                self.graph.add((card_uri, MTGO.card_subtype, Literal(subtype)))

        if "supertypes" in card_info:
            for supertype in card_info["supertypes"]:
                self.graph.add((card_uri, MTGO.card_supertype, Literal(supertype)))

        # Colors
        if "colors" in card_info:
            for color in card_info["colors"]:
                self.graph.add((card_uri, MTGO.color, Literal(color)))

        if "colorIdentity" in card_info:
            for color in card_info["colorIdentity"]:
                self.graph.add((card_uri, MTGO.color_identity, Literal(color)))

        # Rarity
        if "rarity" in card_info:
            self.graph.add((card_uri, MTGO.rarity, Literal(card_info["rarity"])))

        # Mana cost and CMC
        if "manaCost" in card_info:
            self.graph.add((card_uri, MTGO.mana_cost, Literal(card_info["manaCost"])))

        if "manaValue" in card_info:
            self.graph.add(
                (
                    card_uri,
                    MTGO.converted_mana_cost,
                    Literal(card_info["manaValue"], datatype=XSD.decimal),
                )
            )

        # Oracle text and rules text
        if "text" in card_info:
            self.graph.add((card_uri, MTGO.oracle_text, Literal(card_info["text"])))

        if "originalText" in card_info:
            self.graph.add(
                (card_uri, MTGO.rules_text, Literal(card_info["originalText"]))
            )

        # Power/Toughness for creatures
        if "power" in card_info:
            self.graph.add((card_uri, MTGO.power, Literal(card_info["power"])))

        if "toughness" in card_info:
            self.graph.add((card_uri, MTGO.toughness, Literal(card_info["toughness"])))

        # Loyalty for planeswalkers
        if "loyalty" in card_info:
            self.graph.add((card_uri, MTGO.loyalty, Literal(card_info["loyalty"])))

        # Keywords
        if "keywords" in card_info:
            for keyword in card_info["keywords"]:
                self.graph.add((card_uri, MTGO.ability_keyword, Literal(keyword)))

        # Set information
        if "setCode" in card_info:
            self.graph.add((card_uri, MTGO.set_code, Literal(card_info["setCode"])))

        if set_name:
            self.graph.add((card_uri, MTGO.card_set, Literal(set_name)))

        if "number" in card_info:
            self.graph.add(
                (card_uri, MTGO.collector_number, Literal(card_info["number"]))
            )

    def serialize(self, format="turtle", destination=RDF_FILEPATH):
        self.graph.serialize(destination=destination, format=format)

    def transform(self):
        print("Converting to RDF...")
        for set_name, set_info in tqdm(self.data["data"].items()):
            for card_info in set_info["cards"]:
                self.add_card(card_info, set_name)

        print("Conversion completed.")

        print("Serialization started...")
        self.serialize()
        print("RDF data serialized successfully.")


if __name__ == "__main__":
    foo = Transformer()
    foo.transform()
