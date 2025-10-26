import time
from speakeasypy import Chatroom, EventType, Speakeasy

class ChatbotHandler:
    def __init__(self, username: str, password: str, data_handler, sparql_handler, embedding_handler, query_handler):
        self.speakeasy = Speakeasy(host="https://speakeasy.ifi.uzh.ch", username=username, password=password)
        self.data_handler = data_handler
        self.sparql_handler = sparql_handler
        self.embedding_handler = embedding_handler
        self.query_handler = query_handler

        self.speakeasy.login()
        self.speakeasy.register_callback(self.on_new_message, EventType.MESSAGE)
        self.speakeasy.register_callback(self.on_new_reaction, EventType.REACTION)
        print("Chatbot initialized and ready to chat!")

    def listen(self):
        self.speakeasy.start_listening()

    def on_new_reaction(self, reaction: str, message_ordinal: int, room: Chatroom):
        print(f"[{self.get_time()}] Received reaction '{reaction}' on message #{message_ordinal} in room {room.room_id}")
        room.post_messages(f"Thanks for reacting with '{reaction}'! 👍")

    def on_new_message(self, message: str, room: Chatroom):
        print(f"[{self.get_time()}] Processing message in room {room.room_id}: {message}")
        if not self.data_handler.graph:
            room.post_messages("⚠️ Sorry, the knowledge graph isn't loaded yet. I can't process queries right now.")
            return

        head_ent, pred_ent = self.query_handler.find_entities_in_query(message)[0][0], self.query_handler.find_relations_in_query(message)[0][0]
        if not head_ent or not pred_ent:
            room.post_messages("❓ I'm sorry, I couldn't identify the entity or relation in your query. Could you please rephrase?")
            return

        self.sparql_handler.run_sparql_for_prompt(head_ent, pred_ent, room)

        room.post_messages("\n🔎 Now searching the knowledge graph using embeddings...")
        try:
            best_ent_fwd, best_lbl_fwd, best_ent_rev, best_lbl_rev = self.embedding_handler.run_embedding_search(head_ent, pred_ent)
        except KeyError as e:
            room.post_messages(
                f"⚠️ Couldn't perform embedding search. The entity or relation isn't in my embedding data: {e}"
            )
        except Exception as e:
            room.post_messages(f"⚠️ Oops, something went wrong during the embedding search: {e}")

        if best_lbl_fwd:
            room.post_messages(f"Best match: {best_lbl_fwd}")
        else:
            room.post_messages(f"I found a match, but it doesn't have a label. Entity: {best_ent_fwd}")


    @staticmethod
    def get_time() -> str:
        return time.strftime("%H:%M:%S, %d-%m-%Y", time.localtime())