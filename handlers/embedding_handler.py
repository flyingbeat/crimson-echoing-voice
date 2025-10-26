from speakeasypy import Chatroom
from sklearn.metrics import pairwise_distances


class EmbeddingHandler:
    def __init__(self, data_handler):
        self.data_handler = data_handler

    def run_embedding_search(self, head_ent, pred_ent):
        head_emb = self.data_handler.entity_emb[self.data_handler.ent2id[head_ent]]
        pred_emb = self.data_handler.relation_emb[self.data_handler.rel2id[pred_ent]]

        def find_nearest(target_emb):
            dist = pairwise_distances(target_emb.reshape(1, -1), self.data_handler.entity_emb).reshape(-1)
            best_idx = int(dist.argmin())
            best_ent = self.data_handler.id2ent[best_idx]
            best_label = self.data_handler.ent2lbl.get(best_ent)
            return best_ent, best_label

        best_ent_fwd, best_lbl_fwd = find_nearest(head_emb + pred_emb)
        best_ent_rev, best_lbl_rev = find_nearest(head_emb - pred_emb)

        return best_ent_fwd, best_lbl_fwd, best_ent_rev, best_lbl_rev
