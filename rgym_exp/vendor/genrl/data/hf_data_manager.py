from typing import Any, Iterable, Sequence

import torch
from datasets import VerificationMode, load_dataset
from transformers import AutoTokenizer, DataCollatorWithPadding

from rgym_exp.vendor.genrl.data.data_manager import TokenizedDataManager


class _TokenizedTextDataset(torch.utils.data.IterableDataset):
    def __init__(self, dataset, tokenizer, name):
        self.dataset = dataset
        self.tokenizer = tokenizer
        self.name = name

    def __iter__(self):
        for example in self.dataset:
            yield self.tokenizer(example[self.name])


class SerialHuggingFaceDataManager(TokenizedDataManager):
    def __init__(
        self,
        path_or_name: str,
        tokenizer_path_or_name: str,
        batch_size: int,
        text_field_name: str = "text",
        access_token: str | None = None,
        num_workers: int = 0,
        tokenizer_kwargs: dict[str, Any] | None = None,
    ):
        self.path_or_name = path_or_name
        self.tokenizer_path_or_name = tokenizer_path_or_name
        self.batch_size = batch_size
        self.text_field_name = text_field_name
        self.access_token = access_token
        self.num_workers = num_workers
        self.tokenizer_kwargs = tokenizer_kwargs
        self._train_iterator = None

    def initialize(self):
        _ = self.tokenizer
        self._train_iterator = iter(self.train_data_loader)

    def get_data_loader(self, path_or_name, partition):
        dataset = _TokenizedTextDataset(
            load_dataset(
                path_or_name,
                streaming=True,
                split=partition,
                verification_mode=VerificationMode.NO_CHECKS,
            ),
            self.tokenizer,
            self.text_field_name,
        )
        return torch.utils.data.DataLoader(
            dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            collate_fn=DataCollatorWithPadding(tokenizer=self.tokenizer),
        )

    @property
    def train_data_loader(self):
        return self.get_data_loader(self.path_or_name, "train")

    @property
    def tokenizer(self):
        return AutoTokenizer.from_pretrained(
            self.tokenizer_path_or_name,
            token=self.access_token,
            padding_side="left",
            **(self.tokenizer_kwargs or {}),
        )

    def encode(self, text: str) -> Any:
        return self.tokenizer.encode(text)

    def decode(self, tokens: Any) -> str:
        return self.tokenizer.decode(tokens)

    def train_batch(self) -> Any:
        if self._train_iterator is None:
            self._train_iterator = iter(self.train_data_loader)
        try:
            batch = next(self._train_iterator)
        except StopIteration as _:
            self._train_iterator = iter(self.train_data_loader)
            batch = next(self._train_iterator)
        return batch

    def eval_data(self, name: str | None = None) -> Iterable[dict[str, Any]]:
        """Return iterable to eval data."""
        name = name or "validation"
        return self.get_data_loader(self.path_or_name, name)
