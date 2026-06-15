"""Script untuk prediksi sentimen berita crypto menggunakan model lokal."""

try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
except ImportError:
    raise ImportError("Jalankan: pip install transformers torch")

MODEL_PATH = "model/model_crypto_sentiment"

LABEL_MAP = {
    0: "bearish",
    1: "neutral",
    2: "bullish",
}


def predict(text: str) -> str:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128,
    )

    with torch.no_grad():
        outputs = model(**inputs)

    pred = outputs.logits.argmax(1).item()
    return LABEL_MAP[pred]


if __name__ == "__main__":
    text = "Bitcoin is pumping hard after ETF approval"
    result = predict(text)
    print(f"Text : {text}")
    print(f"Label: {result}")
