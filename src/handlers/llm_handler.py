import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Iterator, Optional

from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResponseFormat(Enum):
    TEXT = "text"
    JSON = "json_object"


@dataclass
class PromptTemplate:
    system: str = """Strictly follow these rules:
    1) You should be good in conversation, friendly and welcoming
    2) Do not use prior knowledge, give response to query by using the context provided
    3) you should only answer questions related to movies
    4) Keep your answers short
    """
    context: str = ""
    user_prefix: str = "Given this information, please answer the question: "
    user_suffix: str = ""
    assistant_prefix: Optional[str] = None

    def format(self, prompt: str) -> Dict[str, str]:
        formatted_context = ""
        if self.context:
            formatted_context = (
                "We have provided context information below:\n"
                "------------------------------------------\n"
                f"{self.context}\n"
                "------------------------------------------\n\n"
            )

        formatted_user = (
            f"{formatted_context}{self.user_prefix}{prompt} {self.user_suffix}".strip()
        )

        return {
            "system": self.system,
            "user": formatted_user,
            "assistant_prefix": self.assistant_prefix,
        }


class LLMHandler:

    def __init__(
        self,
        llm_service_endpoint: str = "http://localhost:8080",
        default_model: str = "local-model",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        self.llm_service_endpoint = llm_service_endpoint
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries

        self.llm_client = OpenAI(
            base_url=f"{llm_service_endpoint}/v1", api_key="not-needed", timeout=timeout
        )

        self.default_template = PromptTemplate()

        self.progress_callback: Optional[Callable] = None

        logger.info(f"LLMHandler initialized with endpoint: {llm_service_endpoint}")

    def set_prompt_template(self, template: PromptTemplate):
        self.default_template = template
        logger.info("Prompt template updated")

    def set_progress_callback(self, callback: Callable[[str, Optional[float]], None]):
        self.progress_callback = callback

    def prompt(
        self,
        prompt: str,
        context: Optional[str] = None,
        template: Optional[PromptTemplate] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        response_format: ResponseFormat = ResponseFormat.TEXT,
        **kwargs,
    ) -> str:
        template = template or self.default_template
        template.context = context or template.context
        model = model or self.default_model

        formatted = template.format(prompt)
        logger.info(f"Prompt formatted for model {formatted}")

        messages = [
            {"role": "system", "content": formatted["system"]},
            {"role": "user", "content": formatted["user"]},
        ]

        self._update_progress("Preparing request")

        try:
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
                **kwargs,
            }

            if response_format == ResponseFormat.JSON:
                request_params["response_format"] = {"type": "json_object"}

            self._update_progress("Sending request to LLM")

            if stream:
                return self._handle_streaming_response(request_params, formatted.get("assistant_prefix"))
            else:
                return self._handle_standard_response(request_params, formatted.get("assistant_prefix"))

        except Exception as e:
            logger.error(f"Error during LLM request: {e}")
            self._update_progress(f"Error: {str(e)}")
            raise

    def prompt_stream(
        self,
        prompt: str,
        context: Optional[str] = None,
        template: Optional[PromptTemplate] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> Iterator[str]:
        template = template or self.default_template
        template.context = context or template.context
        model = model or self.default_model

        formatted = template.format(prompt)

        messages = [
            {"role": "system", "content": formatted["system"]},
            {"role": "user", "content": formatted["user"]},
        ]

        self._update_progress("Starting stream")

        try:
            stream = self.llm_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            first_chunk = True
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content

                    if first_chunk and formatted["assistant_prefix"]:
                        content = f"{formatted['assistant_prefix']}{content}"
                        first_chunk = False

                    yield content

            self._update_progress("Stream complete")

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            self._update_progress(f"Stream error: {str(e)}")
            raise

    def _handle_standard_response(
        self, request_params: Dict[str, Any], assistant_prefix: Optional[str] = None
    ) -> str:
        retries = 0
        while retries < self.max_retries:
            try:
                self._update_progress(f"Waiting for response (attempt {retries + 1})")

                response = self.llm_client.chat.completions.create(**request_params)

                self._update_progress("Processing response")

                result = response.choices[0].message.content

                if assistant_prefix:
                    result = f"{assistant_prefix}{result}"

                self._update_progress("Complete")

                logger.info(f"Response received: {len(result)} characters")
                return result

            except Exception as e:
                retries += 1
                logger.warning(f"Attempt {retries} failed: {e}")
                if retries >= self.max_retries:
                    raise
                time.sleep(2**retries)

    def _handle_streaming_response(
        self, request_params: Dict[str, Any], assistant_prefix: Optional[str] = None
    ) -> str:
        self._update_progress("Starting stream")

        stream = self.llm_client.chat.completions.create(**request_params)

        result_chunks = []
        chunk_count = 0

        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                result_chunks.append(content)
                chunk_count += 1

                self._update_progress(f"Receiving stream (chunk {chunk_count})")

        result = "".join(result_chunks)

        if assistant_prefix:
            result = f"{assistant_prefix}{result}"

        self._update_progress("Stream complete")

        logger.info(
            f"Streamed response: {len(result)} characters in {chunk_count} chunks"
        )
        return result

    def _update_progress(self, status: str, progress: Optional[float] = None):
        if self.progress_callback:
            self.progress_callback(status, progress)
        if progress is not None:
            logger.debug(f"Progress: {status} ({progress:.1%})")
        else:
            logger.debug(f"Status: {status}")

    def health_check(self) -> bool:
        try:
            models = self.llm_client.models.list()
            logger.info(
                f"Health check passed. Available models: {[m.id for m in models]}"
            )
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
