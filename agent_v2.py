import os
import signal
import time
import csv
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from rdflib import Graph, Namespace, RDFS
from speakeasypy import Chatroom, EventType, Speakeasy
from sklearn.metrics import pairwise_distances

DEFAULT_HOST_URL = "https://speakeasy.ifi.uzh.ch"
GRAPH_PATH = "/space_mounts/atai-hs25/dataset/graph.nt"
DATA_DIR = "/space_mounts/atai-hs25/dataset/embeddings"
QUERY_TIMEOUT_SECONDS = 10

ENTITY_EMBEDS_PATH = os.path.join(DATA_DIR, 'entity_embeds.npy')
RELATION_EMBEDS_PATH = os.path.join(DATA_DIR, 'relation_embeds.npy')
ENTITY_IDS_PATH = os.path.join(DATA_DIR, 'entity_ids.del')
RELATION_IDS_PATH = os.path.join(DATA_DIR, 'relation_ids.del')

WD = Namespace('http://www.wikidata.org/entity/')
WDT = Namespace('http://www.wikidata.org/prop/direct/')
DDIS = Namespace('http://ddis.ch/atai/')
SCHEMA = Namespace('http://schema.org/')


class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException(f"Query execution timed out after {QUERY_TIMEOUT_SECONDS} seconds.")


class Agent:
    def __init__(self, username: str, password: str):
        self.username = username
        self.speakeasy = Speakeasy(host=DEFAULT_HOST_URL, username=username, password=password)
        self.graph = self._load_graph(GRAPH_PATH)
        self._load_embedding_data()

        self.speakeasy.login()

        self.speakeasy.register_callback(self.on_new_message, EventType.MESSAGE)
        self.speakeasy.register_callback(self.on_new_reaction, EventType.REACTION)
        print("Agent initialized and ready.")

    def listen(self):
        self.speakeasy.start_listening()

    def on_new_reaction(self, reaction: str, message_ordinal: int, room: Chatroom):
        print(f"[{self.get_time()}] Reaction '{reaction}' on message #{message_ordinal} in room {room.room_id}")
        room.post_messages(f"👍 Thanks for your reaction: '{reaction}'")

    def on_new_message(self, message: str, room: Chatroom):
        print(f"[{self.get_time()}] New message in room {room.room_id}: \n {message}")

        if not self.graph:
            room.post_messages("⚠️ Graph is not loaded. Cannot process any queries.")
            return

        self._handle_prompt(message, room)

    def _handle_prompt(self, prompt: str, room: Chatroom):
        parts = [p.strip() for p in prompt.split(',')]
        if len(parts) != 2:
            room.post_messages("Invalid prompt format. Please use the format: `Entity Label, Relation Label`")
            return

        head_label, pred_label = parts

        try:
            head_ent = self.lbl2ent.get(head_label)
            if not head_ent:
                room.post_messages(f"Sorry, I could not find an entity with the label '{head_label}'.")
                return

            pred_ent = self.lbl2ent.get(pred_label)
            if not pred_ent:
                room.post_messages(f"Sorry, I could not find a relation with the label '{pred_label}'.")
                return
        except Exception as e:
            room.post_messages(f"An error occurred while looking up entities: {e}")
            return

        self._run_sparql_for_prompt(head_ent, pred_ent, room)
        self._run_embedding_search(head_ent, pred_ent, room)

    def _run_sparql_for_prompt(self, head_ent, pred_ent, room: Chatroom):
        query = f"""
            SELECT ?objLabel WHERE {{
                <{head_ent}> <{pred_ent}> ?obj .
                ?obj rdfs:label ?objLabel .
            }}
        """
        room.post_messages(
            f"🔎 Searching the knowledge graph for `{head_ent.split('/')[-1]}` → `{pred_ent.split('/')[-1]}`...")
        self._execute_sparql_query(query, room, is_internal=True)

    def _run_embedding_search(self, head_ent, pred_ent, room: Chatroom):
        room.post_messages("\n🧠 Now, searching with embeddings to find the most plausible answers...")
        try:
            head_emb = self.entity_emb[self.ent2id[head_ent]]
            pred_emb = self.relation_emb[self.rel2id[pred_ent]]

            lhs = head_emb + pred_emb
            dist = pairwise_distances(lhs.reshape(1, -1), self.entity_emb).reshape(-1)
            most_likely_indices = dist.argsort()
            print(most_likely_indices)

            results = pd.DataFrame([
                (self.ent2lbl.get(self.id2ent[idx], "N/A"), f"{dist[idx]:.4f}", rank + 1)
                for rank, idx in enumerate(most_likely_indices[:10])],
                columns=('Label', 'Score', 'Rank'))

            response = "Here are the top 10 most plausible results from the embedding search:\n"

            for _, row in results.iterrows():
                response += f"Rank {row['Rank']}: {row['Label']} (Score: {row['Score']})\n"

            room.post_messages(response)

        except KeyError as e:
            room.post_messages(
                f"⚠️ Could not perform embedding search. Entity or relation not found in embedding dictionary: `{e}`")
        except Exception as e:
            room.post_messages(f"⚠️ An error occurred during the embedding search: {e}")

    def _execute_sparql_query(self, query: str, room: Chatroom, is_internal: bool = False):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(QUERY_TIMEOUT_SECONDS)

        try:
            results = self.graph.query(query)
            result_list = [", ".join(str(item) for item in row) for row in results]

            if not result_list:
                if not is_internal:
                    room.post_messages("⚠️ I ran the query, but there are no results.")
                else:
                    room.post_messages("I didn't find any direct results in the knowledge graph.")
                return

            response_text = self._format_results(result_list)
            room.post_messages(response_text)

        except TimeoutException as e:
            room.post_messages(f"⚠️ Sorry, the query took too long to execute. {e}")
        except Exception as e:
            room.post_messages(f"⚠️ Sorry, I couldn't process that query. Error: {e}")
        finally:
            signal.alarm(0)

    def _load_embedding_data(self):
        print("Loading embedding data...")
        try:
            self.entity_emb = np.load(ENTITY_EMBEDS_PATH)
            self.relation_emb = np.load(RELATION_EMBEDS_PATH)

            with open(ENTITY_IDS_PATH, 'r') as f:
                self.ent2id = {Namespace(ent): int(idx) for idx, ent in csv.reader(f, delimiter='\t')}
            self.id2ent = {v: k for k, v in self.ent2id.items()}

            with open(RELATION_IDS_PATH, 'r') as f:
                self.rel2id = {Namespace(rel): int(idx) for idx, rel in csv.reader(f, delimiter='\t')}
            self.id2rel = {v: k for k, v in self.rel2id.items()}

            if self.graph:
                self.ent2lbl = {ent: str(lbl) for ent, lbl in self.graph.subject_objects(RDFS.label)}
                self.lbl2ent = {lbl: ent for ent, lbl in self.ent2lbl.items()}

            print("Embedding data loaded successfully.")
        except FileNotFoundError as e:
            print(f"Error loading embedding data: {e}. Embedding features will be disabled.")
            self.entity_emb = None
        except Exception as e:
            print(f"A general error occurred while loading embedding data: {e}")

    @staticmethod
    def _load_graph(path: str) -> Graph | None:
        print("Loading graph...")
        graph = Graph()
        try:
            graph.parse(path, format="nt")
            print("Graph loaded successfully.")
            return graph
        except FileNotFoundError:
            print(f"Error: Graph file not found at {path}")
        except Exception as e:
            print(f"Failed to load graph: {e}")
        return None

    @staticmethod
    def _format_results(results: list[str]) -> str:
        if len(results) == 1:
            return f"Here is the result I found: {results[0]}"
        formatted = "\n- ".join(results)
        return f"I found multiple results:\n- {formatted}"

    @staticmethod
    def get_time() -> str:
        return time.strftime("%H:%M:%S, %d-%m-%Y", time.localtime())


if __name__ == "__main__":
    load_dotenv()

    if os.name == 'nt':
        print("Warning: The query timeout feature is not supported on Windows.")

    agent = Agent(os.getenv("SPEAKEASY_USERNAME", ""), os.getenv("SPEAKEASY_PASSWORD", ""))
    agent.listen()