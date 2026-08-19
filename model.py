"""BiRefNet model loading and in-memory background removal."""

from __future__ import annotations

import hashlib
import hmac
from threading import Lock
from typing import Any, Final, Protocol, runtime_checkable

from PIL import Image


MODEL_ID: Final = "ZhengPeng7/BiRefNet_dynamic"
MODEL_REVISION: Final = "280306042f57b7a33854319da62fd86aaa89ec4c"
MODEL_WEIGHTS_SHA256: Final = (
    "e3d2e4884e51ff30f0cd630edc6b1e41b06b7f23a0a2a5169f7b7cb33a711c2d"
)

# BiRefNet_dynamic was trained with arbitrary shapes up to 2304 px. Keeping a
# slightly smaller ceiling makes CPU inference and concurrent server memory use
# predictable while the alpha mask is still returned at the original size.
MAX_INFERENCE_SIDE: Final = 2048


@runtime_checkable
class BackgroundRemover(Protocol):
    """Small interface used by the API and replaced by a fake in smoke tests."""

    def remove_background(self, image: Image.Image) -> Image.Image:
        """Return an RGBA image with the same size as ``image``."""


class BiRefNetRemover:
    """Inference wrapper around the pinned BiRefNet_dynamic checkpoint."""

    def __init__(self, model: Any, torch_module: Any, device: Any) -> None:
        self._model = model
        self._torch = torch_module
        self._device = device
        self._dtype = (
            torch_module.float16 if device.type == "cuda" else torch_module.float32
        )
        # A single model is intentionally shared by the process. Serializing
        # inference avoids concurrent GPU memory spikes in this small MVP.
        self._inference_lock = Lock()

    @classmethod
    def load(cls) -> "BiRefNetRemover":
        """Download/load exactly one pinned model and select CUDA or CPU."""

        # Heavy imports stay inside the production loader. Importing app.py for
        # smoke tests therefore never imports torch or downloads model weights.
        import torch
        from transformers import AutoModelForImageSegmentation

        torch.set_float32_matmul_precision("high")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _verify_model_weights()

        model = AutoModelForImageSegmentation.from_pretrained(
            MODEL_ID,
            revision=MODEL_REVISION,
            code_revision=MODEL_REVISION,
            trust_remote_code=True,
            use_safetensors=True,
        )
        model.to(device)
        model.eval()
        if device.type == "cuda":
            model.half()
        else:
            # The checkpoint is stored with FP16 parameters. PyTorch CPU input
            # tensors are FP32, so make weights/biases explicit FP32 as well.
            model.float()

        return cls(model=model, torch_module=torch, device=device)

    @staticmethod
    def _scaled_inference_size(size: tuple[int, int]) -> tuple[int, int]:
        """Return a bounded (width, height), with both sides divisible by 32."""

        width, height = size
        scale = min(1.0, MAX_INFERENCE_SIDE / max(width, height))
        scaled_width = max(32, int(width * scale))
        scaled_height = max(32, int(height * scale))
        scaled_width = max(32, (scaled_width // 32) * 32)
        scaled_height = max(32, (scaled_height // 32) * 32)
        return scaled_width, scaled_height

    def _to_model_tensor(self, image: Image.Image) -> Any:
        """Apply the normalization from the official BiRefNet model card."""

        import numpy as np

        inference_size = self._scaled_inference_size(image.size)
        if image.size != inference_size:
            image = image.resize(inference_size, Image.Resampling.LANCZOS)

        pixels = np.asarray(image, dtype=np.float32) / 255.0
        tensor = self._torch.from_numpy(pixels).permute(2, 0, 1).unsqueeze(0)
        mean = self._torch.tensor((0.485, 0.456, 0.406)).view(1, 3, 1, 1)
        std = self._torch.tensor((0.229, 0.224, 0.225)).view(1, 3, 1, 1)
        tensor = (tensor - mean) / std
        return tensor.to(device=self._device, dtype=self._dtype)

    def remove_background(self, image: Image.Image) -> Image.Image:
        """Run BiRefNet and return a transparent RGBA image in memory."""

        import numpy as np

        source = image.convert("RGB")
        original_size = source.size

        with self._inference_lock:
            input_tensor = self._to_model_tensor(source)
            with self._torch.inference_mode():
                # The official API returns multi-scale logits; the last item
                # is the final foreground prediction.
                logits = self._model(input_tensor)[-1]
                mask_tensor = logits.sigmoid()[0].squeeze().float().cpu()

        if mask_tensor.ndim != 2:
            raise RuntimeError("BiRefNet returned an invalid mask shape")

        mask_array = (
            mask_tensor.clamp(0, 1).mul(255).round().to(self._torch.uint8).numpy()
        )
        mask = Image.fromarray(np.asarray(mask_array, dtype=np.uint8))
        if mask.size != original_size:
            mask = mask.resize(original_size, Image.Resampling.LANCZOS)

        result = source.convert("RGBA")
        result.putalpha(mask)
        return result


def load_background_remover() -> BiRefNetRemover:
    """Production loader kept as a function for startup patching in tests."""

    return BiRefNetRemover.load()


def _verify_model_weights() -> None:
    """Download the pinned safetensors file and verify its recorded SHA-256."""

    from huggingface_hub import hf_hub_download

    weight_path = hf_hub_download(
        repo_id=MODEL_ID,
        filename="model.safetensors",
        revision=MODEL_REVISION,
    )
    digest = hashlib.sha256()
    with open(weight_path, "rb") as weights:
        for chunk in iter(lambda: weights.read(1024 * 1024), b""):
            digest.update(chunk)

    actual = digest.hexdigest()
    if not hmac.compare_digest(actual, MODEL_WEIGHTS_SHA256):
        raise RuntimeError("Pinned BiRefNet weights failed SHA-256 verification")
