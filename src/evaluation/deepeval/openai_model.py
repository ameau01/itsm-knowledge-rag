"""Custom OpenAI judge model.

DeepEval's native GPTModel validates the model id against a hard-coded allowlist that
lags new releases (older builds reject gpt-5.x). This wraps the OpenAI API directly so
ANY model string works, bypassing that allowlist. Used only as a fallback when the
native model rejects the requested id (see deepeval_judge._resolve_judge_model), so when
DeepEval already supports the model natively we keep its well-tested path.

deepeval + openai are imported lazily, so importing this module needs neither.
"""

from __future__ import annotations

from deepeval.models import DeepEvalBaseLLM


class OpenAIJudgeModel(DeepEvalBaseLLM):
    def __init__(self, model: str, api_key: str | None = None) -> None:
        self._model = model
        self._api_key = api_key
        self._client = None
        self._aclient = None

    def get_model_name(self) -> str:
        return self._model

    def load_model(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def _async_client(self):
        if self._aclient is None:
            from openai import AsyncOpenAI
            self._aclient = AsyncOpenAI(api_key=self._api_key)
        return self._aclient

    @staticmethod
    def _parse(client, model, prompt, schema):
        """Structured output via the OpenAI SDK, tolerant of the beta→stable move."""
        parse = getattr(getattr(client.chat.completions, "parse", None), "__call__", None)
        if parse is None:
            parse = client.beta.chat.completions.parse  # older SDKs
        resp = parse(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format=schema,
        )
        return resp.choices[0].message.parsed

    def generate(self, prompt: str, schema=None):
        client = self.load_model()
        if schema is not None:
            return self._parse(client, self._model, prompt, schema)
        resp = client.chat.completions.create(
            model=self._model, messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content

    async def a_generate(self, prompt: str, schema=None):
        client = self._async_client()
        if schema is not None:
            try:
                parse = client.chat.completions.parse
            except AttributeError:
                parse = client.beta.chat.completions.parse
            resp = await parse(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                response_format=schema,
            )
            return resp.choices[0].message.parsed
        resp = await client.chat.completions.create(
            model=self._model, messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
