"""Local chat LLM (Qwen2.5-1.5B-Instruct by default) with optional LoRA adapter.

Loading is lazy and the model is shared per process. ``is_available()`` lets callers fall
back to extractive answers when no GPU / weights are present, so the MVP never crashes.
"""

from __future__ import annotations

import threading
from functools import lru_cache
from pathlib import Path

from cybersec_nlp import config


class LocalLLM:
    def __init__(self, model_id: str = config.LLM_MODEL, adapter_path: Path | None = None) -> None:
        self.model_id = model_id
        self.adapter_path = adapter_path
        self._model = None
        self._tokenizer = None
        self._lock = threading.Lock()

    @staticmethod
    def is_available() -> bool:
        try:
            import torch
        except ImportError:
            return False
        return torch.cuda.is_available()

    def _load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self._tokenizer.padding_side = "left"
        model = AutoModelForCausalLM.from_pretrained(
            self.model_id, dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
        )
        if self.adapter_path is not None:
            from peft import PeftModel

            model = PeftModel.from_pretrained(model, str(self.adapter_path))
        self._model = model.eval()

    def unload(self) -> None:
        """Free GPU memory (e.g. before fine-tuning); the model reloads lazily on the next call."""
        import gc

        import torch

        self._model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            self._load()
        return self._tokenizer

    @property
    def model(self):
        if self._model is None:
            self._load()
        return self._model

    def chat(self, messages: list[dict[str, str]], max_new_tokens: int = 256,
             temperature: float = 0.0, top_p: float = 0.9) -> str:
        return self.chat_batch([messages], max_new_tokens, temperature, top_p)[0]

    def chat_batch(self, conversations: list[list[dict[str, str]]], max_new_tokens: int = 256,
                   temperature: float = 0.0, top_p: float = 0.9) -> list[str]:
        """Greedy decoding when ``temperature == 0``, nucleus sampling otherwise."""
        import torch

        with self._lock:
            prompts = [self.tokenizer.apply_chat_template(c, tokenize=False, add_generation_prompt=True)
                       for c in conversations]
            inputs = self.tokenizer(prompts, return_tensors="pt", padding=True).to(self.model.device)
            sampling = temperature > 0
            with torch.no_grad():
                output = self.model.generate(
                    **inputs, max_new_tokens=max_new_tokens, do_sample=sampling,
                    temperature=temperature if sampling else None, top_p=top_p if sampling else None,
                    top_k=None, pad_token_id=self.tokenizer.eos_token_id,
                )
            new_tokens = output[:, inputs["input_ids"].shape[1]:]
            return [t.strip() for t in self.tokenizer.batch_decode(new_tokens, skip_special_tokens=True)]


@lru_cache(maxsize=2)
def get_llm(adapter_path: str | None = None) -> LocalLLM:
    return LocalLLM(adapter_path=Path(adapter_path) if adapter_path else None)
