import time
import logging
from typing import Any, Dict
from openai import OpenAI
from benchmark.llms.base import BaseLlm
from benchmark.llms.exceptions import LlmException
from benchmark.utils import TIME_TO_FIRST_BYTE, TIME_TO_FULL_RESPONSE


logger = logging.getLogger()


class OpenAILlm(BaseLlm):
    def __init__(self, model_id: str) -> None:
        super().__init__()
        self.client = OpenAI()
        self.system_prompt = {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "You are a sci-fi writer born in Argentina. Your goal is to write "
                        "a short story in no more than 3 paragraphs about a topic defined by the user"
                    ),
                }
            ],
        }
        self.model_id = model_id

    def get_story(self, topic: str) -> Dict[str, Any]:
        max_length = 2000

        user_message = {"role": "user", "content": topic}
        messages = [self.system_prompt, user_message]

        logger.debug(f"About to write an story about: {topic}")

        start_time = time.perf_counter_ns() / 1e9

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=1,
                max_tokens=max_length,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
        except Exception as e:
            logger.exception(e)
            raise LlmException() from e

        end_time = round((time.perf_counter_ns() / 1e9) - start_time, 3)
        TIME_TO_FIRST_BYTE.labels(
            provider="openai",
            model=self.model_id,
            mode="write",
        ).observe(end_time)
        TIME_TO_FULL_RESPONSE.labels(
            provider="openai",
            model=self.model_id,
            mode="write",
        ).observe(end_time)

        story = response.choices[0].message.content

        return {"topic": topic, "story": story}

    def stream_story(self, topic: str):
        max_length = 2000

        user_message = {"role": "user", "content": topic}
        messages = [self.system_prompt, user_message]

        logger.debug(f"About to stream an story about: {topic}")

        start_time = time.perf_counter_ns() / 1e9

        try:
            stream = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=1,
                max_tokens=max_length,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stream=True,
            )

        except Exception as e:
            logger.exception(f"Error reading LLM response {e}")
            raise LlmException() from e

        for i, chunk in enumerate(stream):
            if i == 0:
                ttfb = round((time.perf_counter_ns() / 1e9) - start_time, 3)
                TIME_TO_FIRST_BYTE.labels(
                    provider="openai",
                    model=self.model_id,
                    mode="streaming",
                ).observe(ttfb)
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

        end_time = round((time.perf_counter_ns() / 1e9) - start_time, 3)
        TIME_TO_FULL_RESPONSE.labels(
            provider="openai",
            model=self.model_id,
            mode="streaming",
        ).observe(end_time)
