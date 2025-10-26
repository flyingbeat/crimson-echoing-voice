import csv
import os

import numpy as np
from rdflib import RDFS, Graph, Namespace, URIRef
from SPARQLWrapper import JSON, SPARQLWrapper


class DataHandler:
    def __init__(self, sparql_endpoint, data_dir):
        self.sparql_endpoint = sparql_endpoint
        self.data_dir = data_dir
        self.entity_embeds_path = os.path.join(data_dir, "entity_embeds.npy")
        self.relation_embeds_path = os.path.join(data_dir, "relation_embeds.npy")
        self.entity_ids_path = os.path.join(data_dir, "entity_ids.del")
        self.relation_ids_path = os.path.join(data_dir, "relation_ids.del")
        self.graph = self._load_graph(self.sparql_endpoint)
        self._load_embedding_data()

    def _load_embedding_data(self):
        print("Loading embedding data...")
        try:
            self.entity_emb = np.load(self.entity_embeds_path)
            self.relation_emb = np.load(self.relation_embeds_path)

            with open(self.entity_ids_path, "r") as f:
                self.ent2id = {
                    str(ent): int(idx) for idx, ent in csv.reader(f, delimiter="\t")
                }
            self.id2ent = {v: k for k, v in self.ent2id.items()}

            with open(self.relation_ids_path, "r") as f:
                self.rel2id = {
                    str(rel): int(idx) for idx, rel in csv.reader(f, delimiter="\t")
                }
            self.id2rel = {v: k for k, v in self.rel2id.items()}

            if self.graph:
                self.ent2lbl = self._get_entity_labels()
                self.lbl2ent = {lbl: ent for ent, lbl in self.ent2lbl.items()}

            print("Embedding data loaded successfully.")
        except FileNotFoundError as e:
            print(
                f"Error loading embedding data: {e}. Embedding features will be disabled."
            )
            self.entity_emb = None
        except Exception as e:
            print(f"Unexpected error while loading embedding data: {e}")

    def _get_entity_labels(self):
        """Get entity to label mappings using SPARQL query."""
        try:
            query = """
            SELECT ?entity ?label
            WHERE {
                ?entity <http://www.w3.org/2000/01/rdf-schema#label> ?label .
            }
            """
            self.graph.setQuery(query)
            results = self.graph.queryAndConvert()

            ent2lbl = {}
            for result in results["results"]["bindings"]:
                entity_uri = str(result["entity"]["value"])
                label = str(result["label"]["value"])
                ent2lbl[entity_uri] = label

            return ent2lbl
        except Exception as e:
            print(f"Error fetching entity labels: {e}")
            return {}

    @staticmethod
    def _load_graph(endpoint: str) -> Graph | None:
        print("Loading knowledge graph...")
        try:
            graph = SPARQLWrapper(endpoint)
            graph.setReturnFormat(JSON)
            print("Knowledge graph loaded successfully.")
            return graph
        except Exception as e:
            print(f"Failed to load graph: {e}")
        return None
