from speakeasypy import Chatroom
from sklearn.metrics import pairwise_distances


class EmbeddingHandler:
    def __init__(self, data_handler):
        self.data_handler = data_handler

    def run_embedding_search(self, head_ent, pred_ent, room: Chatroom):
        room.post_messages("\n🔎 Now searching the knowledge graph using embeddings...")
        try:
            head_emb = self.data_handler.entity_emb[self.data_handler.ent2id[head_ent]]
            pred_emb = self.data_handler.relation_emb[self.data_handler.rel2id[pred_ent]]

            lhs = head_emb + pred_emb
            dist = pairwise_distances(lhs.reshape(1, -1), self.data_handler.entity_emb).reshape(-1)
            best_idx = int(dist.argmin())
            best_ent = self.data_handler.id2ent[best_idx]

            label = self.data_handler.ent2lbl.get(best_ent)
            if label:
                room.post_messages(f"Best match: {label}")
            else:
                room.post_messages(f"I found a match, but it doesn't have a label. Entity: {best_ent}")

        except KeyError as e:
            room.post_messages(
                f"⚠️ Couldn't perform embedding search. The entity or relation isn't in my embedding data: {e}"
            )
        except Exception as e:
            room.post_messages(f"⚠️ Oops, something went wrong during the embedding search: {e}")
