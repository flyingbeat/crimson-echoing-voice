import time

from speakeasypy import Chatroom, EventType, Speakeasy

from handlers.data_handler import DataHandler
from handlers.embedding_handler import EmbeddingHandler
from handlers.llm_handler import LLMHandler
from handlers.message_handler import MessageHandler
from handlers.recommendation_handler import RecommendationHandler
from handlers.sparql_handler import SparqlHandler


class ChatbotHandler:
    def __init__(
        self,
        username: str,
        password: str,
        data_handler: DataHandler,
        sparql_handler: SparqlHandler,
        embedding_handler: EmbeddingHandler,
        message_handler: MessageHandler,
        llm_handler: LLMHandler,
        recommendation_handler: RecommendationHandler,
    ):
        self.speakeasy = Speakeasy(
            host="https://speakeasy.ifi.uzh.ch", username=username, password=password
        )
        self.data_handler = data_handler
        self.sparql_handler = sparql_handler
        self.embedding_handler = embedding_handler
        self.message_handler = message_handler
        self.llm_handler = llm_handler
        self.recommendation_handler = recommendation_handler

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

        entities = self.message_handler.find_entities_in_query(message)
        res = self.recommendation_handler.get_recommendations(
            entity_ids=[str(ent[0]) for ent in entities]
        )
        # room.post_messages(res)
        return
        relations = self.message_handler.find_relations_in_query(message)

        entity = entities[0] if entities else None
        relation = relations[0] if relations else None

        entity_id = str(entity[0]) if entity else None
        entity_label = entity[2] if entity else None
        entity_description = entity[3] if entity else None
        relation_id = str(relation[0]) if relation else None
        relation_label = relation[2] if relation else None

        if not entity_id or not relation_id:
            room.post_messages(
                "❓ I'm sorry, I couldn't identify the entity or relation in your query. Could you please rephrase?"
            )
            return

        msg_lower = message.lower()
        run_factual = "embedding" not in msg_lower
        run_embedding = "factual" not in msg_lower

        # initialize variables used later so LLM context building is safe even if blocks are skipped
        subject_responses = []
        object_responses = []
        (
            best_object_response_label,
            best_subject_response_label,
            best_object_response_id,
            best_subject_response_id,
        ) = (None, None, None, None)
        room.post_messages(
            f"Let me figure out the answer for your question about the {relation_label} of {entity_label} ({entity_description})..."
        )
        if run_factual:
            room.post_messages("🔎 Searching the knowledge graph factually...")
            try:
                subject_responses, object_responses = (
                    self.sparql_handler.run_sparql_for_prompt(entity_id, relation_id)
                )
                non_wikidata_items = []
                if object_responses and not (
                    non_wikidata_items := [
                        item
                        for item in object_responses
                        if not item.startswith("http://www.wikidata.org/entity/")
                    ]
                ):
                    room.post_messages(
                        f"🔎 I found a match, but it doesn't have a label. Entity: {" and ".join(object_responses)}"
                    )
                else:
                    room.post_messages(
                        f"🔎 Factual response: {' and '.join(non_wikidata_items) if non_wikidata_items else 'No valid responses found.'}"
                    )
            except Exception as e:
                room.post_messages(
                    f"⚠️ Oops, something went wrong during the SPARQL query: {e}"
                )

        if run_embedding:
            room.post_messages(f"📊 Searching for embedding-based answer...")
            try:
                (
                    best_object_response_id,
                    best_object_response_label,
                    best_subject_response_id,
                    best_subject_response_label,
                ) = self.embedding_handler.run_embedding_search(entity_id, relation_id)
                if best_object_response_label:
                    room.post_messages(
                        f"📊 Best match: {best_object_response_label} (type: {self.sparql_handler.get_instance_of(best_object_response_id).split('/')[-1]})"
                    )
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

        try:
            factual_context = (
                f"{" and ".join(object_responses)} is {relation_label} of {entity_label} ({entity_description})"
                if object_responses
                else ""
            ) + (
                f"{" and ".join(subject_responses)} is {relation_label} of {entity_label} ({entity_description})"
                if subject_responses
                else ""
            )

            embedding_context = (
                f"{best_object_response_label} is {relation_label} of {entity_label} ({entity_description})"
                if best_object_response_label
                else ""
            ) + (
                f"{best_subject_response_label} is {relation_label} of {entity_label} ({entity_description})"
                if best_subject_response_label
                else ""
            )

            context = factual_context if factual_context else embedding_context

            if context:

                room.post_messages("🤖 Generating response with LLM...")
                query_prefixes = [
                    "Please answer this question with an embedding approach:",
                    "Please answer this question with a factual approach:",
                    "Please answer this question:",
                ]

                question = message
                for query_prefix in query_prefixes:
                    if query_prefix in message:
                        question = message.split(query_prefix, 1)[1].strip()
                        break

                llm_response = self.llm_handler.prompt(question, context=context)

                room.post_messages(llm_response)

        except Exception as e:
            room.post_messages(
                f"⚠️ Oops, something went wrong during the LLM generation: {e}"
            )

    @staticmethod
    def get_time() -> str:
        return time.strftime("%H:%M:%S, %d-%m-%Y", time.localtime())
