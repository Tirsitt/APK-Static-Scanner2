import io
import zipfile
import numpy as np
from PIL import Image

MANIFEST_NAME = "AndroidManifest.xml"
DEX_NAME = "classes.dex"
IMAGE_SIZE = 224  
FIXED_CANVAS_SIDE = 255  


class ApkExtractionError(Exception):
    """Raised when the uploaded file isn't a usable APK."""


def extract_manifest_and_dex(apk_bytes: bytes) -> tuple[bytes, bytes]:
    """Pull raw AndroidManifest.xml and classes.dex bytes out of an APK (a zip file)."""
    try:
        with zipfile.ZipFile(io.BytesIO(apk_bytes)) as z:
            names = z.namelist()
            if MANIFEST_NAME not in names:
                raise ApkExtractionError("AndroidManifest.xml not found — is this a valid APK?")
            if DEX_NAME not in names:
                raise ApkExtractionError("classes.dex not found — is this a valid APK?")
            manifest_bytes = z.read(MANIFEST_NAME)
            dex_bytes = z.read(DEX_NAME)
    except zipfile.BadZipFile as e:
        raise ApkExtractionError("File isn't a valid zip/APK.") from e
    return manifest_bytes, dex_bytes


def _bytes_to_square_matrix(data: bytes, side: int = FIXED_CANVAS_SIDE) -> np.ndarray:
    """
    Fit byte data into a FIXED side x side matrix: zero-padded if shorter,
    truncated to the first side*side bytes if longer.
    """
    arr = np.frombuffer(data, dtype=np.uint8)
    total = side * side
    fixed = np.zeros(total, dtype=np.uint8)
    n = min(len(arr), total)
    fixed[:n] = arr[:n]
    return fixed.reshape(side, side)


def build_image(manifest_bytes: bytes, dex_bytes: bytes) -> Image.Image:
    """Combine manifest + dex byte matrices into one resized RGB image."""
    manifest_matrix = _bytes_to_square_matrix(manifest_bytes)
    dex_matrix = _bytes_to_square_matrix(dex_bytes)

    manifest_img = Image.fromarray(manifest_matrix, mode="L").resize(
        (IMAGE_SIZE, IMAGE_SIZE), Image.NEAREST
    )
    dex_img = Image.fromarray(dex_matrix, mode="L").resize(
        (IMAGE_SIZE, IMAGE_SIZE), Image.NEAREST
    )

    r = np.array(manifest_img, dtype=np.uint8)
    g = np.array(dex_img, dtype=np.uint8)
    b = np.zeros_like(r)  

    rgb = np.stack([r, g, b], axis=-1)
    return Image.fromarray(rgb, mode="RGB")


def apk_to_image(apk_bytes: bytes) -> Image.Image:
    """Full pipeline: raw APK bytes in, classifier-ready RGB image out."""
    manifest_bytes, dex_bytes = extract_manifest_and_dex(apk_bytes)
    return build_image(manifest_bytes, dex_bytes)