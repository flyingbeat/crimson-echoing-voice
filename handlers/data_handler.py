import os
import csv
import numpy as np
from rdflib import Graph, Namespace, RDFS, URIRef

class DataHandler:
    def __init__(self, graph_path, data_dir):
        self.graph_path = graph_path
        self.data_dir = data_dir
        self.entity_embeds_path = os.path.join(data_dir, 'entity_embeds.npy')
        self.relation_embeds_path = os.path.join(data_dir, 'relation_embeds.npy')
        self.entity_ids_path = os.path.join(data_dir, 'entity_ids.del')
        self.relation_ids_path = os.path.join(data_dir, 'relation_ids.del')
        self.graph = self._load_graph(self.graph_path)
        self._load_embedding_data()

    def _load_embedding_data(self):
        print("Loading embedding data...")
        try:
            self.entity_emb = np.load(self.entity_embeds_path)
            self.relation_emb = np.load(self.relation_embeds_path)

            with open(self.entity_ids_path, 'r') as f:
                self.ent2id = {URIRef(ent): int(idx) for idx, ent in csv.reader(f, delimiter='\t')}
            self.id2ent = {v: k for k, v in self.ent2id.items()}

            with open(self.relation_ids_path, 'r') as f:
                self.rel2id = {URIRef(rel): int(idx) for idx, rel in csv.reader(f, delimiter='\t')}
            self.id2rel = {v: k for k, v in self.rel2id.items()}

            if self.graph:
                self.ent2lbl = {ent: str(lbl) for ent, lbl in self.graph.subject_objects(RDFS.label)}
                self.lbl2ent = {lbl: ent for ent, lbl in self.ent2lbl.items()}

            print("Embedding data loaded successfully.")
        except FileNotFoundError as e:
            print(f"Error loading embedding data: {e}. Embedding features will be disabled.")
            self.entity_emb = None
        except Exception as e:
            print(f"Unexpected error while loading embedding data: {e}")

    @staticmethod
    def _load_graph(path: str) -> Graph | None:
        print("Loading knowledge graph...")
        graph = Graph()
        try:
            graph.parse(path, format="nt")
            print("Knowledge graph loaded successfully.")
            return graph
        except FileNotFoundError:
            print(f"Error: Graph file not found at {path}")
        except Exception as e:
            print(f"Failed to load graph: {e}")
        return None