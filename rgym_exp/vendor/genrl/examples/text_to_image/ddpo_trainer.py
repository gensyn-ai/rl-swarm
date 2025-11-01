import gc
import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Callable, List, Optional
from warnings import warn

import torch
from torch.amp import GradScaler, autocast
from trl import DDPOConfig, DefaultDDPOStableDiffusionPipeline

from rgym_exp.vendor.genrl.data.data_manager import DataManager
from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger
from rgym_exp.vendor.genrl.logging_utils.ml_logger import ImageLoggerMixin
from rgym_exp.vendor.genrl.rewards import RewardManager
from rgym_exp.vendor.genrl.state import GameState
from rgym_exp.vendor.genrl.trainer.base_trainer import TrainerModule


@dataclass
class DDPOSample:
    prompts: List[str]
    images: torch.Tensor
    prompt_embeds: torch.Tensor
    timesteps: torch.Tensor
    latents: torch.Tensor
    next_latents: torch.Tensor
    log_probs: torch.Tensor
    negative_prompt_embeds: torch.Tensor


class DDPOTrainer(TrainerModule, ImageLoggerMixin):
    """
    The DDPOTrainer uses Deep Diffusion Policy Optimization to optimise diffusion models.
    Note, this trainer is heavily inspired by the work here: https://github.com/kvablack/ddpo-pytorch
    As of now only Stable Diffusion based pipelines are supported

    Attributes:
        **config** (`DDPOConfig`) -- Configuration object for DDPOTrainer. Check the documentation of `PPOConfig` for more
         details.
        **sd_pipeline** (`DDPOStableDiffusionPipeline`) -- Stable Diffusion pipeline to be used for training.
        **image_samples_hook** (Optional[Callable[[Any, Any, Any], Any]]) -- Hook to be called to log images
        **rank** (int) -- The rank of this trainer in a distributed setup (default: 0).
    """

    def __init__(
        self,
        config: DDPOConfig,
        sd_pipeline: DefaultDDPOStableDiffusionPipeline,
        output_dir: str = "outputs",
        image_samples_hook: Optional[Callable[[Any, Any, Any], Any]] = None,
        rank: int = 0,
        optimizer: Optional[torch.optim.Optimizer] = None,
    ):
        if image_samples_hook is None:
            warn("No image_samples_hook provided; no images will be logged")

        self.config = config
        self.output_dir = output_dir
        self.image_samples_callback = image_samples_hook
        self.rank = rank

        # number of timesteps within each trajectory to train on
        self.num_train_timesteps = int(
            self.config.sample_num_steps * self.config.train_timestep_fraction
        )

        # Initialize device
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
        get_logger().info(f"Using device: {self.device}")

        # Set up mixed precision training
        self.mixed_precision = self.config.mixed_precision
        self.grad_scaler = GradScaler() if self.mixed_precision == "fp16" else None

        # Set up gradient accumulation
        self.gradient_accumulation_steps = (
            self.config.train_gradient_accumulation_steps * self.num_train_timesteps
        )
        self.sync_gradients = True  # Flag to indicate when to apply gradients

        is_okay, message = self._config_check()
        if not is_okay:
            raise ValueError(message)

        # Set up tracking/logging
        self.is_main_process = True  # In single-device setting, this is always True

        if self.config.log_with:
            log_dir = os.path.join(self.output_dir, "logs", f"rank_{self.rank}")
            os.makedirs(log_dir, exist_ok=True)
            self.init_tracker(log_dir, self.config.log_with)

        # Adjust output directory to include rank
        if self.output_dir:
            self.output_dir = os.path.join(
                self.output_dir, f"rank_{self.rank}_checkpoints"
            )
            os.makedirs(self.output_dir, exist_ok=True)
        else:
            self.output_dir = os.path.join("outputs", f"rank_{self.rank}_checkpoints")
            os.makedirs(self.output_dir, exist_ok=True)

        get_logger().info(f"\n{config}")

        self.sd_pipeline = sd_pipeline

        self.sd_pipeline.set_progress_bar_config(
            position=1,
            disable=False,  # Always show progress in single device mode
            leave=False,
            desc="Timestep",
            dynamic_ncols=True,
        )

        # For mixed precision training we cast all non-trainable weights (vae, non-lora text_encoder and non-lora unet) to half-precision
        # as these weights are only used for inference, keeping weights in full precision is not required.
        if self.mixed_precision == "fp16":
            inference_dtype = torch.float16
        elif self.mixed_precision == "bf16":
            inference_dtype = torch.bfloat16
        else:
            inference_dtype = torch.float32

        self.sd_pipeline.vae.to(self.device, dtype=inference_dtype)
        self.sd_pipeline.text_encoder.to(self.device, dtype=inference_dtype)
        self.sd_pipeline.unet.to(self.device, dtype=inference_dtype)

        trainable_layers = self.sd_pipeline.get_trainable_layers()

        self.optimizer = optimizer or torch.optim.AdamW(
            (
                trainable_layers.parameters()
                if not isinstance(trainable_layers, list)
                else trainable_layers
            ),
            lr=self.config.train_learning_rate,
            betas=(self.config.train_adam_beta1, self.config.train_adam_beta2),
            weight_decay=self.config.train_adam_weight_decay,
            eps=self.config.train_adam_epsilon,
        )

        self.neg_prompt_embed = self.sd_pipeline.text_encoder(
            self.sd_pipeline.tokenizer(
                (
                    [""]
                    if self.config.negative_prompts is None
                    else self.config.negative_prompts
                ),
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=self.sd_pipeline.tokenizer.model_max_length,
            ).input_ids.to(self.device)
        )[0]

        # Set up autocast for mixed precision training
        self.use_autocast = self.mixed_precision in ["fp16", "bf16"]
        self.autocast = self.sd_pipeline.autocast or (
            lambda: (
                autocast(self.device, dtype=inference_dtype)
                if self.use_autocast
                else torch.no_op()
            )
        )

        self.trainable_layers = trainable_layers

        # Move trainable layers to device if they're not already there
        if isinstance(trainable_layers, list):
            for layer in trainable_layers:
                if hasattr(layer, "to"):
                    layer.to(self.device)
        else:
            if hasattr(trainable_layers, "to"):
                trainable_layers.to(self.device)

        self.first_epoch = 0

        self.global_step = 0
        self.accumulated_step = 0

    def generate(self, prompts: List[str]) -> DDPOSample:
        """
        Generate samples from the model

        Args:
            prompts List[str]: List of prompts to generate samples for

        Returns:
            DDPOSample: A dataclass containing samples for training and reward calculation
        """
        batch_size = len(prompts)
        self.sd_pipeline.unet.eval()

        sample_neg_prompt_embeds = self.neg_prompt_embed.repeat(batch_size, 1, 1)

        prompt_ids = self.sd_pipeline.tokenizer(
            prompts,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=self.sd_pipeline.tokenizer.model_max_length,
        ).input_ids.to(self.device)
        prompt_embeds = self.sd_pipeline.text_encoder(prompt_ids)[0]

        with self.autocast():
            sd_output = self.sd_pipeline(
                prompt_embeds=prompt_embeds,
                negative_prompt_embeds=sample_neg_prompt_embeds,
                num_inference_steps=self.config.sample_num_steps,
                guidance_scale=self.config.sample_guidance_scale,
                eta=self.config.sample_eta,
                output_type="pt",
            )

            images = sd_output.images
            latents = sd_output.latents
            log_probs = sd_output.log_probs

        latents = torch.stack(latents, dim=1)  # (batch_size, num_steps + 1, ...)
        log_probs = torch.stack(log_probs, dim=1)  # (batch_size, num_steps, 1)
        timesteps = self.sd_pipeline.scheduler.timesteps.repeat(
            batch_size, 1
        )  # (batch_size, num_steps)

        sample = DDPOSample(
            prompts=prompts,
            images=images,
            prompt_embeds=prompt_embeds,
            timesteps=timesteps,
            latents=latents[:, :-1],  # each entry is the latent before timestep t
            next_latents=latents[:, 1:],  # each entry is the latent after timestep t
            log_probs=log_probs,
            negative_prompt_embeds=sample_neg_prompt_embeds,
        )

        # Return as a dataclass for better type hinting and organization
        return sample

    def step(
        self, game_state: GameState, reward_manager: RewardManager, global_step: int
    ) -> int:
        """
        Perform a single step of training.

        Args:
            game_state (GameState): The current game state containing the generated outputs.
            reward_manager (RewardManager): The reward manager that contains the computed rewards.

        Side Effects:
            - Model weights are updated
            - Logs the statistics
            - If `self.image_samples_callback` is not None, it will be called with the prompt_image_pairs, global_step, and tracker.

        Returns:
            int: The updated global step
        """
        # Get the latest generated outputs from the game state - this will be a list of outputs from all agents
        latest_actions = game_state.get_stage_actions(0)  # single stage game
        samples = self.batch_actions(latest_actions)

        # Get rewards from the reward manager instead of computing them internally, we only have one stage
        rewards, rewards_metadata = reward_manager.rewards[0]

        # Log metrics
        log_data = {
            "train/epoch": global_step,
            "train/reward_mean": rewards.mean().item(),
            "train/reward_std": rewards.std().item(),
        }

        self.log(log_data, global_step)

        advantages = (rewards - rewards.mean()) / (rewards.std() + 1e-8)

        # In single-device mode, advantages correspond directly to our samples
        samples["advantages"] = torch.as_tensor(advantages).to(self.device)

        total_batch_size, num_timesteps = samples["timesteps"].shape

        for inner_epoch in range(self.config.train_num_inner_epochs):
            # shuffle samples along batch dimension
            perm = torch.randperm(total_batch_size, device=self.device)
            samples = {k: v[perm] for k, v in samples.items()}

            # shuffle along time dimension independently for each sample
            perms = torch.stack(
                [
                    torch.randperm(num_timesteps, device=self.device)
                    for _ in range(total_batch_size)
                ]
            )

            for key in ["timesteps", "latents", "next_latents", "log_probs"]:
                samples[key] = samples[key][
                    torch.arange(total_batch_size, device=self.device)[:, None],
                    perms,
                ]

            original_keys = samples.keys()
            original_values = samples.values()
            # rebatch them as user defined train_batch_size is different from sample_batch_size
            reshaped_values = [
                v.reshape(-1, self.config.train_batch_size, *v.shape[1:])
                for v in original_values
            ]

            # Transpose the list of original values
            transposed_values = zip(*reshaped_values)
            # Create new dictionaries for each row of transposed values
            samples_batched = [
                dict(zip(original_keys, row_values)) for row_values in transposed_values
            ]

            self.sync_gradients = False
            self.sd_pipeline.unet.train()
            global_step = self._train_batched_samples(
                inner_epoch, game_state.round, global_step, samples_batched
            )
            # ensure optimization step at the end of the inner epoch if needed
            if not self.sync_gradients:
                # Step with scaler if using mixed precision, otherwise regular step
                if self.grad_scaler is not None:
                    self.grad_scaler.step(self.optimizer)
                    self.grad_scaler.update()
                else:
                    self.optimizer.step()
                self.optimizer.zero_grad()

        if (
            global_step != 0
            and global_step % self.config.save_freq == 0
            and self.is_main_process
        ):
            self._save_checkpoint(global_step)

        unscaled_rewards = rewards * rewards_metadata["std"] + rewards_metadata["mean"]
        self.log({"train/rewards": unscaled_rewards.mean().item()}, global_step)
        self.cleanup()
        return global_step

    def calculate_loss(
        self, latents, timesteps, next_latents, log_probs, advantages, embeds
    ):
        """
        Calculate the loss for a batch of an unpacked sample

        Args:
            latents (torch.Tensor):
                The latents sampled from the diffusion model, shape: [batch_size, num_channels_latents, height, width]
            timesteps (torch.Tensor):
                The timesteps sampled from the diffusion model, shape: [batch_size]
            next_latents (torch.Tensor):
                The next latents sampled from the diffusion model, shape: [batch_size, num_channels_latents, height, width]
            log_probs (torch.Tensor):
                The log probabilities of the latents, shape: [batch_size]
            advantages (torch.Tensor):
                The advantages of the latents, shape: [batch_size]
            embeds (torch.Tensor):
                The embeddings of the prompts, shape: [2*batch_size or batch_size, ...]
                Note: the "or" is because if train_cfg is True, the expectation is that negative prompts are concatenated to the embeds

        Returns:
            loss (torch.Tensor), approx_kl (torch.Tensor), clipfrac (torch.Tensor)
            (all of these are of shape (1,))
        """
        with self.autocast():
            if self.config.train_cfg:
                noise_pred = self.sd_pipeline.unet(
                    torch.cat([latents] * 2),
                    torch.cat([timesteps] * 2),
                    embeds,
                ).sample
                noise_pred_uncond, noise_pred_text = noise_pred.chunk(2)
                noise_pred = noise_pred_uncond + self.config.sample_guidance_scale * (
                    noise_pred_text - noise_pred_uncond
                )
            else:
                noise_pred = self.sd_pipeline.unet(
                    latents,
                    timesteps,
                    embeds,
                ).sample
            # compute the log prob of next_latents given latents under the current model

            scheduler_step_output = self.sd_pipeline.scheduler_step(
                noise_pred,
                timesteps,
                latents,
                eta=self.config.sample_eta,
                prev_sample=next_latents,
            )

            log_prob = scheduler_step_output.log_probs

        advantages = torch.clamp(
            advantages,
            -self.config.train_adv_clip_max,
            self.config.train_adv_clip_max,
        )

        ratio = torch.exp(log_prob - log_probs)

        loss = self.loss(advantages, self.config.train_clip_range, ratio)

        approx_kl = 0.5 * torch.mean((log_prob - log_probs) ** 2)

        clipfrac = torch.mean(
            (torch.abs(ratio - 1.0) > self.config.train_clip_range).float()
        )

        return loss, approx_kl, clipfrac

    def loss(
        self,
        advantages: torch.Tensor,
        clip_range: float,
        ratio: torch.Tensor,
    ):
        unclipped_loss = -advantages * ratio
        clipped_loss = -advantages * torch.clamp(
            ratio,
            1.0 - clip_range,
            1.0 + clip_range,
        )
        return torch.mean(torch.maximum(unclipped_loss, clipped_loss))

    def _setup_optimizer(self, trainable_layers_parameters):
        if self.config.train_use_8bit_adam:
            import bitsandbytes

            optimizer_cls = bitsandbytes.optim.AdamW8bit
        else:
            optimizer_cls = torch.optim.AdamW

        return optimizer_cls(
            trainable_layers_parameters,
            lr=self.config.train_learning_rate,
            betas=(self.config.train_adam_beta1, self.config.train_adam_beta2),
            weight_decay=self.config.train_adam_weight_decay,
            eps=self.config.train_adam_epsilon,
        )

    def _train_batched_samples(self, inner_epoch, epoch, global_step, batched_samples):
        """
        Train on a batch of samples. Main training segment

        Args:
            inner_epoch (int): The current inner epoch
            epoch (int): The current epoch
            global_step (int): The current global step
            batched_samples (list[dict[str, torch.Tensor]]): The batched samples to train on

        Side Effects:
            - Model weights are updated
            - Logs the statistics

        Returns:
            global_step (int): The updated global step
        """
        info = defaultdict(list)

        for _i, sample in enumerate(batched_samples):

            if self.config.train_cfg:
                # concat negative prompts to sample prompts to avoid two forward passes
                embeds = torch.cat(
                    [sample["negative_prompt_embeds"], sample["prompt_embeds"]]
                )
            else:
                embeds = sample["prompt_embeds"]
            for j in range(self.num_train_timesteps):

                with self.autocast():
                    # Compute loss with mixed precision if enabled
                    loss, approx_kl, clipfrac = self.calculate_loss(
                        sample["latents"][:, j],
                        sample["timesteps"][:, j],
                        sample["next_latents"][:, j],
                        sample["log_probs"][:, j],
                        sample["advantages"],
                        embeds,
                    )

                    # Scale loss for gradient accumulation if needed
                    if self.gradient_accumulation_steps > 1:
                        loss = loss / self.gradient_accumulation_steps

                info["approx_kl"].append(approx_kl)
                info["clipfrac"].append(clipfrac)
                info["loss"].append(loss)

                # Backward pass with mixed precision if enabled
                if self.grad_scaler is not None:
                    self.grad_scaler.scale(loss).backward()
                else:
                    loss.backward()

                self.accumulated_step += 1

                # Step the optimizer when we've accumulated enough gradients
                if self.accumulated_step % self.gradient_accumulation_steps == 0:
                    # Apply gradient clipping if configured
                    if self.config.train_max_grad_norm > 0:
                        if self.grad_scaler is not None:
                            self.grad_scaler.unscale_(self.optimizer)

                        # Get parameters to clip
                        parameters = (
                            self.trainable_layers.parameters()
                            if not isinstance(self.trainable_layers, list)
                            else self.trainable_layers
                        )
                        torch.nn.utils.clip_grad_norm_(
                            parameters, self.config.train_max_grad_norm
                        )

                    # Step with scaler if using mixed precision, otherwise regular step
                    if self.grad_scaler is not None:
                        self.grad_scaler.step(self.optimizer)
                        self.grad_scaler.update()
                    else:
                        self.optimizer.step()

                    self.optimizer.zero_grad()
                    self.sync_gradients = (
                        True  # set here so we know we did an update for the inner epoch
                    )

                    # Calculate mean of collected metrics
                    metrics = {
                        "train/" + k: torch.mean(torch.tensor(v)).item()
                        for k, v in info.items()
                    }

                    # Add epoch info
                    metrics.update({"epoch": epoch, "inner_epoch": inner_epoch})

                    self.log(metrics, global_step)

                    self.accumulated_step = 0
                    global_step += 1

        return global_step

    def batch_actions(self, actions):
        all_samples = []
        all_prompt_image_pairs = []

        # Iterate through all agents to populate all_samples and all_prompt_image_pairs
        for agent in actions:
            # Iterate through each batch for this agent
            for batch_idx in actions[agent]:
                # Each batch may have multiple generations
                for node_idx, node in enumerate(actions[agent][batch_idx]):
                    all_samples.append(node)  # node is DDPOSample

        prompt_embeds_list = []
        timesteps_list = []
        latents_list = []
        next_latents_list = []
        log_probs_list = []
        negative_prompt_embeds_list = []

        for sample_item in all_samples:
            prompt_embeds_list.append(sample_item.prompt_embeds)
            timesteps_list.append(sample_item.timesteps)
            latents_list.append(sample_item.latents)
            next_latents_list.append(sample_item.next_latents)
            log_probs_list.append(sample_item.log_probs)
            negative_prompt_embeds_list.append(sample_item.negative_prompt_embeds)

        stacked_prompt_embeds = torch.stack(prompt_embeds_list)
        stacked_timesteps = torch.stack(timesteps_list)
        stacked_latents = torch.stack(latents_list)
        stacked_next_latents = torch.stack(next_latents_list)
        stacked_log_probs = torch.stack(log_probs_list)
        stacked_negative_prompt_embeds = torch.stack(negative_prompt_embeds_list)

        batched_samples = DDPOSample(
            prompts=None,
            images=None,
            prompt_embeds=stacked_prompt_embeds,
            timesteps=stacked_timesteps,
            latents=stacked_latents,
            next_latents=stacked_next_latents,
            log_probs=stacked_log_probs,
            negative_prompt_embeds=stacked_negative_prompt_embeds,
        )

        # Convert DDPOSample object to a dictionary to facility inner epoch training and rebatching according to trl logic
        samples = asdict(batched_samples)
        del samples["prompts"]  # not needed for training
        del samples["images"]  # not needed for training

        return samples

    def cleanup(self):
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    def _config_check(self) -> tuple[bool, str]:
        # In single device mode, num_processes is 1
        num_processes = 1  # Without accelerator, we're assuming single-device mode

        samples_per_epoch = (
            self.config.sample_batch_size
            * num_processes
            * self.config.sample_num_batches_per_epoch
        )
        total_train_batch_size = (
            self.config.train_batch_size
            * num_processes
            * self.config.train_gradient_accumulation_steps
        )

        if not self.config.sample_batch_size >= self.config.train_batch_size:
            return (
                False,
                f"Sample batch size ({self.config.sample_batch_size}) must be greater than or equal to the train batch size ({self.config.train_batch_size})",
            )
        if not self.config.sample_batch_size % self.config.train_batch_size == 0:
            return (
                False,
                f"Sample batch size ({self.config.sample_batch_size}) must be divisible by the train batch size ({self.config.train_batch_size})",
            )
        if not samples_per_epoch % total_train_batch_size == 0:
            return (
                False,
                f"Number of samples per epoch ({samples_per_epoch}) must be divisible by the total train batch size ({total_train_batch_size})",
            )
        return True, ""

    def train(
        self,
        game_state: GameState,
        data_manager: DataManager,
        reward_manager: RewardManager,
    ):
        """
        Train the model for a given number of epochs
        """
        global_step = self.global_step
        global_step = self.step(game_state, reward_manager, global_step)
        self.global_step = global_step

    def save(self, save_directory):
        self.sd_pipeline.save_pretrained(save_directory)
        torch.save(
            self.optimizer.state_dict(), os.path.join(save_directory, "optimizer.pt")
        )
        torch.save(self.config, os.path.join(save_directory, "config.pt"))

        trainer_state = {
            "global_step": getattr(self, "global_step", 0),
            "first_epoch": getattr(self, "first_epoch", 0),
            "rank": getattr(self, "rank", 0),
            "output_dir": getattr(self, "output_dir", "outputs"),
        }
        torch.save(trainer_state, os.path.join(save_directory, "trainer_state.pt"))

    def load(cls, load_directory):
        optimizer = torch.load(os.path.join(load_directory, "optimizer.pt"))
        trainer_state = torch.load(os.path.join(load_directory, "trainer_state.pt"))
        return cls(
            config=torch.load(os.path.join(load_directory, "config.pt")),
            sd_pipeline=DefaultDDPOStableDiffusionPipeline.from_pretrained(
                load_directory
            ),
            output_dir=trainer_state["output_dir"],
            rank=trainer_state["rank"],
            optimizer=optimizer,
        )

    def _save_checkpoint(self, global_step):
        name = f"checkpoint_{global_step}"
        self.sd_pipeline.save_pretrained(os.path.join(self.output_dir, name))

    @torch.no_grad()
    def evaluate(
        self,
        game_state: GameState,
        data_manager: DataManager,
        reward_manager: RewardManager,
    ):
        seed = 42
        generator = torch.Generator(device="cuda")
        generator = generator.manual_seed(seed)
        eval_data_loader = data_manager.get_eval_data()
        prompts = next(iter(eval_data_loader))
        prompts = [
            x[1].environment_states for x in prompts
        ]  # prompts are tuples (batch idx, WorldState)

        images = self.sd_pipeline(
            prompts, generator=generator, output_type="pt"
        ).images.cpu()

        reward_fn = reward_manager.dispatch_reward_fn(
            reward_manager.round, 0
        )  # single stage game
        rewards, scalers_dict = reward_fn.evaluation(prompts, images)
        rewards = rewards * scalers_dict["std"] + scalers_dict["mean"]

        self.log_images(images, prompts, reward_manager.round)
        # Log evaluation metrics
        reward_mean = rewards.mean().item()
        get_logger().info(
            f"Evaluation at round {reward_manager.round}: mean reward = {reward_mean:.4f}"
        )
        self.log({"eval/reward": reward_mean}, reward_manager.round)

        return

    def cleanup(self):
        self.cleanup_trackers()
