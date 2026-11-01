"""
Android APK Malware Classifier

Uses the trained MobileNetV2 model created in the Kaggle training notebook.

Training configuration:
- timm model: mobilenetv2_100
- num_classes: 2
- image size: 224x224
- label 0: benign
- label 1: malicious
- RGB input
- blue channel zeroed
- pixel values normalized to [0, 1]
"""

from pathlib import Path

import torch
import torch.nn.functional as F
import timm
from PIL import Image
import numpy as np

IMAGE_SIZE = 224
DEVICE = torch.device("cpu")

DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parent / "model.pth"

_model = None

def load_trained_model(weights_path: str | None = None):
    
    global _model

    weights = Path(weights_path) if weights_path else DEFAULT_WEIGHTS_PATH

    if not weights.exists():
        raise FileNotFoundError(
            f"Model weights not found: {weights}"
        )

    model = timm.create_model(
        "mobilenetv2_100",
        pretrained=False,
        num_classes=2
    )

    state_dict = torch.load(
        weights,
        map_location=DEVICE,
        weights_only=True
    )

    model.load_state_dict(state_dict)

    model.to(DEVICE)
    model.eval()

    _model = model

    print(f"Loaded malware detection model from: {weights}")

def _prepare_image(image: Image.Image) -> torch.Tensor:
    
    image = image.convert("RGB")
    image = image.resize((IMAGE_SIZE, IMAGE_SIZE))

    arr = np.array(image, dtype=np.float32)

    arr[:, :, 2] = 0.0

    arr = arr / 255.0

    tensor = torch.from_numpy(arr).permute(2, 0, 1)

    tensor = tensor.unsqueeze(0)

    return tensor.to(DEVICE)

def classify(
    image: Image.Image,
    manifest_bytes: bytes | None = None
) -> tuple[str, float]:
    
    global _model

    if _model is None:
        load_trained_model()

    tensor = _prepare_image(image)

    with torch.no_grad():
        outputs = _model(tensor)

        probabilities = F.softmax(outputs, dim=1)

        predicted_class = probabilities.argmax(dim=1).item()
        confidence = probabilities[0, predicted_class].item()

    if predicted_class == 0:
        label = "benign"
    else:
        label = "malicious"

    return label, round(confidence, 4)