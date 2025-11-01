from typing import Any

import torch
import torch.nn as nn
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import EntryNotFoundError
from transformers import CLIPModel, CLIPProcessor

from rgym_exp.vendor.genrl.state import GameState


class AestheticScorer(torch.nn.Module):
    """
    This model attempts to predict the aesthetic score of an image. The aesthetic score
    is a numerical approximation of how much a specific image is liked by humans on average.
    This is from https://github.com/christophschuhmann/improved-aesthetic-predictor
    """

    def __init__(self, *, dtype, model_id, model_filename):
        class MLP(nn.Module):
            def __init__(self):
                super().__init__()
                self.layers = nn.Sequential(
                    nn.Linear(768, 1024),
                    nn.Dropout(0.2),
                    nn.Linear(1024, 128),
                    nn.Dropout(0.2),
                    nn.Linear(128, 64),
                    nn.Dropout(0.1),
                    nn.Linear(64, 16),
                    nn.Linear(16, 1),
                )

            @torch.no_grad()
            def forward(self, embed):
                return self.layers(embed)

        super().__init__()
        self.clip = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
        self.mlp = MLP()
        try:
            cached_path = hf_hub_download(model_id, model_filename)
        except EntryNotFoundError:
            cached_path = os.path.join(model_id, model_filename)
        state_dict = torch.load(
            cached_path, map_location=torch.device("cpu"), weights_only=True
        )
        self.mlp.load_state_dict(state_dict)
        self.dtype = dtype
        self.eval()

    @torch.no_grad()
    def __call__(self, images, prompts, metadata):
        device = next(self.parameters()).device
        inputs = self.processor(images=images, return_tensors="pt", do_rescale=True)
        inputs = {k: v.to(self.dtype).to(device) for k, v in inputs.items()}
        embed = self.clip.get_image_features(**inputs)
        # normalize embedding
        embed = embed / torch.linalg.vector_norm(embed, dim=-1, keepdim=True)
        return self.mlp(embed).squeeze(1)


class CLIPScorer(torch.nn.Module):
    def __init__(self, model_id=None, model_filename=None):
        super().__init__()
        self.model_id = "openai/clip-vit-large-patch14"

        self.clip = CLIPModel.from_pretrained(self.model_id)
        self.processor = CLIPProcessor.from_pretrained(self.model_id)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.compute_dtype = (
            torch.float16 if self.device.type == "cuda" else torch.float32
        )

        self.clip.to(self.device).to(dtype=self.compute_dtype)

        self.eval()

    @torch.no_grad()
    def __call__(
        self, images: torch.Tensor, prompts: list[str], metadata: dict[str, Any]
    ):
        if not isinstance(prompts, list):
            raise TypeError(f"Prompts must be a list of strings, got {type(prompts)}")
        if images.shape[0] != len(prompts):
            raise ValueError(
                f"Number of images ({images.shape[0]}) does not match number of prompts ({len(prompts)})."
            )

        images = images.to(self.device)

        img_inputs = self.processor(images=images, return_tensors="pt", do_rescale=True)
        img_inputs = {
            k: v.to(self.device).to(self.compute_dtype) for k, v in img_inputs.items()
        }

        img_features = self.clip.get_image_features(**img_inputs)
        img_features = img_features / img_features.norm(p=2, dim=-1, keepdim=True)

        text_inputs = self.processor(
            text=prompts, return_tensors="pt", padding=True, truncation=True
        )
        text_input_ids = text_inputs["input_ids"].to(self.device)
        text_attention_mask = text_inputs["attention_mask"].to(self.device)
        text_features = self.clip.get_text_features(
            input_ids=text_input_ids, attention_mask=text_attention_mask
        )
        text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)

        clip_scores = torch.sum(img_features * text_features, dim=-1)

        return clip_scores


class ScorerReward:
    def __init__(self, model_id, model_filename, aesthetic=True):
        self.aesthetic = aesthetic
        self.model_id = model_id
        self.model_filename = model_filename
        if aesthetic:
            self.scorer = AestheticScorer(
                model_id=model_id,
                model_filename=model_filename,
                dtype=torch.float32,
            )
        else:
            self.scorer = CLIPScorer(model_id=model_id, model_filename=model_filename)

        if torch.cuda.is_available():
            self.scorer = self.scorer.cuda()

    def evaluation(self, prompts, images):
        if self.aesthetic:
            images = (images * 255).round().clamp(0, 255).to(torch.uint8)
            scores = self.scorer(images, None, None)
            # scores /= 10
        else:
            scores = self.scorer(images, prompts, None)

        return (scores - scores.mean()) / scores.std(), {
            "mean": scores.mean(),
            "std": scores.std(),
        }

    def __call__(self, game_state: GameState):
        ddpo_samples = game_state.get_stage_actions(0)  # single stage game

        images = []
        prompts = []
        for agent in ddpo_samples:
            for batch_idx in ddpo_samples[agent]:
                for node_idx, _ in enumerate(ddpo_samples[agent][batch_idx]):
                    images.append(ddpo_samples[agent][batch_idx][node_idx].images)
                    prompts.append(ddpo_samples[agent][batch_idx][node_idx].prompts)
        images = torch.stack(images)

        if self.aesthetic:
            images = (images * 255).round().clamp(0, 255).to(torch.uint8)
            scores = self.scorer(images, None, None)
            # scores /= 10
        else:
            scores = self.scorer(images, prompts, None)

        return (scores - scores.mean()) / scores.std(), {
            "mean": scores.mean(),
            "std": scores.std(),
        }
