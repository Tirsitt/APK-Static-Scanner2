import sys
from pathlib import Path

import gradio as gr
import spaces

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from apk_utils import apk_to_image, ApkExtractionError
from model import classify, load_trained_model

load_trained_model()

@spaces.GPU
def analyze_apk(apk_file):
    if apk_file is None:
        return "Lütfen bir APK dosyası yükleyin.", None

    try:
        apk_bytes = open(apk_file, "rb").read()
        image = apk_to_image(apk_bytes)
    except ApkExtractionError as e:
        return f"Hata: {e}", None
    except Exception as e:
        return f"Beklenmeyen hata: {e}", None

    label, confidence = classify(image)

    if label == "malicious":
        verdict = f"⚠️ ZARARLI\nŞüpheli statik gösterge tespit edildi.\n%{confidence*100:.0f} güven"
    else:
        verdict = f"✅ ZARARSIZ\nŞüpheli statik gösterge bulunamadı.\n%{confidence*100:.0f} güven"

    return verdict, image

demo = gr.Interface(
    fn=analyze_apk,
    inputs=gr.File(label="APK dosyasını yükle", file_types=[".apk"]),
    outputs=[
        gr.Textbox(label="Sonuç", lines=4),
        gr.Image(label="Oluşturulan byte-görüntü (debug için)", type="pil"),
    ],
    title="Statik Analiz // Byte-Görüntü Sınıflandırma",
    description=(
        "Bir APK yükleyin. Manifest ve dex baytları doğrudan bir görüntüye "
        "dönüştürülür — çalıştırma yok, emülatör yok — ve bir sınıflandırıcı "
        "bu görüntüyü kötü amaçlı yazılım belirtileri için inceler.\n\n"
        "Sadece statik analiz — dosya asla çalıştırılmaz."
    ),
    flagging_mode="never",
)

if __name__ == "__main__":
    demo.launch()