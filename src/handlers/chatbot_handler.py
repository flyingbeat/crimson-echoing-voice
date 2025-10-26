import time

from speakeasypy import Chatroom, EventType, Speakeasy

from handlers.data_handler import DataHandler
from handlers.embedding_handler import EmbeddingHandler
from handlers.llm_handler import LLMHandler
from handlers.query_handler import QueryHandler
from handlers.sparql_hanlder import SparqlHandler


class ChatbotHandler:
    def __init__(
        self,
        username: str,
        password: str,
        data_handler: DataHandler,
        sparql_handler: SparqlHandler,
        embedding_handler: EmbeddingHandler,
        query_handler: QueryHandler,
        llm_handler: LLMHandler,
    ):
        self.speakeasy = Speakeasy(
            host="https://speakeasy.ifi.uzh.ch", username=username, password=password
        )
        self.data_handler = data_handler
        self.sparql_handler = sparql_handler
        self.embedding_handler = embedding_handler
        self.query_handler = query_handler
        self.llm_handler = llm_handler

        self.speakeasy.login()
        self.speakeasy.register_callback(self.on_new_message, EventType.MESSAGE)
        self.speakeasy.register_callback(self.on_new_reaction, EventType.REACTION)
        print("Chatbot initialized and ready to chat!")

    def listen(self):
        self.speakeasy.start_listening()

    def on_new_reaction(self, reaction: str, message_ordinal: int, room: Chatroom):
        print(
            f"[{self.get_time()}] Received reaction '{reaction}' on message #{message_ordinal} in room {room.room_id}"
        )
        room.post_messages(f"Thanks for reacting with '{reaction}'! 👍")

    def on_new_message(self, message: str, room: Chatroom):
        print(
            f"[{self.get_time()}] Processing message in room {room.room_id}: {message}"
        )
        if not self.data_handler.graph:
            room.post_messages(
                "⚠️ Sorry, the knowledge graph isn't loaded yet. I can't process queries right now."
            )
            return

        entities = self.query_handler.find_entities_in_query(message)
        relations = self.query_handler.find_relations_in_query(message)

        entity = entities[0] if entities else None
        relation = relations[0] if relations else None

        entity_id = str(entity[0]) if entity else None
        entity_label = entity[2] if entity else None
        relation_id = str(relation[0]) if relation else None
        relation_label = relation[2] if relation else None

        if not entity_id or not relation_id:
            room.post_messages(
                "❓ I'm sorry, I couldn't identify the entity or relation in your query. Could you please rephrase?"
            )
            return

        room.post_messages("🔎 Searching the knowledge graph factually...")
        try:
            subject_response, object_response = (
                self.sparql_handler.run_sparql_for_prompt(entity_id, relation_id)
            )
            if object_response and object_response.startswith("http://www.wikidata.org/entity/"):
                room.post_messages(
                    f"🔎 I found a match, but it doesn't have a label. Entity: {object_response}"
                )
            else:
                room.post_messages(f"🔎 Factual response: {object_response}")
        except Exception as e:
            room.post_messages(
                f"⚠️ Oops, something went wrong during the SPARQL query: {e}"
            )

        room.post_messages(f"📊 Searching for embedding-based answer...")
        try:
            (
                best_object_response_id,
                best_object_response_label,
                best_subject_response_id,
                best_subject_response_label,
            ) = self.embedding_handler.run_embedding_search(entity_id, relation_id)
            if best_object_response_label:
                room.post_messages(f"📊 Best match: {best_object_response_label}")
            else:
                room.post_messages(
                    f"📊 I found a match, but it doesn't have a label. Entity: {best_object_response_id}"
                )
        except KeyError as e:
            room.post_messages(
                f"⚠️ Couldn't perform embedding search. The entity or relation isn't in my embedding data: {e}"
            )
        except Exception as e:
            room.post_messages(
                f"⚠️ Oops, something went wrong during the embedding search: {e}"
            )

        room.post_messages("🤖 Generating response with LLM...")
        try:
            factual_context = (
                f"{entity_label} is {relation_label} of {object_response}"
                if object_response
                else ""
            ) + (
                f"{subject_response} is {relation_label} of {entity_label}"
                if subject_response
                else ""
            )

            embedding_context = (
                f"{entity_label} is {relation_label} of {best_object_response_label}"
                if best_object_response_label
                else ""
            ) + (
                f"{best_subject_response_label} is {relation_label} of {entity_label}."
                if best_subject_response_label
                else ""
            )

            llm_response = self.llm_handler.prompt(
                message, context=f"{factual_context}\n{embedding_context}"
            )
            room.post_messages(llm_response)
        except Exception as e:
            room.post_messages(
                f"⚠️ Oops, something went wrong during the LLM generation: {e}"
            )

    @staticmethod
    def get_time() -> str:
        return time.strftime("%H:%M:%S, %d-%m-%Y", time.localtime())
