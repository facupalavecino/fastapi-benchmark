import time
import json
import logging
from typing import Any, Dict
import boto3

from benchmark.llms.base import BaseLlm
from benchmark.llms.exceptions import LlmException
from benchmark.utils import TIME_TO_FIRST_BYTE, TIME_TO_FULL_RESPONSE


logger = logging.getLogger()


class ClaudeBedrockLlm(BaseLlm):

    def __init__(self) -> None:
        super().__init__()
        self.client = boto3.client(
            service_name="bedrock-runtime", region_name="us-east-1"
        )
        self.system_prompt = (
            "You are a sci-fi writer born in Argentina. Your goal is to write "
            "a short story in no more than 3 paragraphs about a topic defined by the user"
        )
        self.model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    def get_story(self, topic: str) -> Dict[str, Any]:

        max_length = 2000

        user_message = {"role": "user", "content": topic}

        messages = [user_message]

        body = json.dumps(
            {
                "messages": messages,
                "system": self.system_prompt,
                "max_tokens": max_length,
                "temperature": 0.4,
                "top_k": 250,
                "top_p": 1,
                "anthropic_version": "bedrock-2023-05-31",
            }
        )

        logger.debug(f"About to write an story about: {topic}")

        start_time = time.perf_counter_ns() / 1e9

        try:
            response: Dict[str, Any] = self.client.invoke_model(
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json",
                body=body,
            )
        except Exception as e:
            logger.exception(e)
            raise LlmException() from e

        story = None

        try:
            response_body = json.loads(response.get("body").read())

        except Exception as e:
            logger.exception(f"Error reading LLM response {e}")
            raise LlmException() from e

        end_time = round((time.perf_counter_ns() / 1e9) - start_time, 3)
        TIME_TO_FIRST_BYTE.labels(provider="bedrock", model=self.model_id).observe(
            end_time
        )
        TIME_TO_FULL_RESPONSE.labels(provider="bedrock", model=self.model_id).observe(
            end_time
        )

        story = response_body["content"][0]["text"]

        return {"topic": topic, "story": story}

    def stream_story(self, topic: str):
        max_length = 2000
        user_message = {"role": "user", "content": topic}
        messages = [user_message]

        body = json.dumps(
            {
                "messages": messages,
                "system": self.system_prompt,
                "max_tokens": max_length,
                "temperature": 0.4,
                "top_k": 250,
                "top_p": 1,
                "anthropic_version": "bedrock-2023-05-31",
            }
        )

        logger.debug(f"About to stream an story about: {topic}")

        start_time = time.perf_counter_ns() / 1e9
        try:
            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id, body=body
            )
            event_stream = response.get("body", {})

            for i, event in enumerate(event_stream):
                if i == 0:
                    ttfb = round((time.perf_counter_ns() / 1e9) - start_time, 3)
                    TIME_TO_FIRST_BYTE.labels(
                        provider="bedrock", model=self.model_id
                    ).observe(ttfb)

                chunk = json.loads(event["chunk"]["bytes"])
                if chunk["type"] == "content_block_delta":
                    yield chunk["delta"].get("text", "")

        except Exception as e:
            logger.exception(f"Error reading LLM response {e}")
            raise LlmException() from e

        end_time = round((time.perf_counter_ns() / 1e9) - start_time, 3)
        TIME_TO_FULL_RESPONSE.labels(provider="bedrock", model=self.model_id).observe(
            end_time
        )
