import logging

from loguru import logger

try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    logging.warning(
        "transformers/torch tidak terinstall. "
        "Jalankan: pip install transformers torch"
    )

CATEGORY_CONFIG = {
    "crypto": {
        "model_path": "Rozirizky/sentiment_analysis_crypto",
        "label_map": {0: "negative", 1: "positive", 2: "neutral"},
        "max_length": 128,
    },
    "forex": {
        "model_path": "Rozirizky/sentiment_analysis_forex",
        "label_map": {0: "bearish", 1: "bullish", 2: "neutral"},
        "max_length": 128,
    },
    "stocks": {
        "model_path": "Rozirizky/sentiment_analys_stoks",
        "label_map": {0: "negative", 1: "positive", 2: "neutral"},
        "max_length": 128,
    },
}


class PredictSentimen:

    _models     = {}
    _tokenizers = {}

    def __init__(self, category: str):
        category = category.lower().strip()

        if category not in CATEGORY_CONFIG:
            available = ", ".join(CATEGORY_CONFIG.keys())
            raise ValueError(
                f"Category '{category}' tidak dikenali. "
                f"Pilihan yang tersedia: {available}"
            )

        self.category   = category
        self.config     = CATEGORY_CONFIG[category]
        self.label_map  = self.config["label_map"]
        self.max_length = self.config["max_length"]
        self._load_model()

    def _load_model(self):
        category   = self.category
        model_path = self.config["model_path"]

        if category not in PredictSentimen._models:
            logger.info(f"[{category.upper()}] Loading model dari '{model_path}'...")
            PredictSentimen._models[category] = (
                AutoModelForSequenceClassification.from_pretrained(model_path)
            )
            PredictSentimen._tokenizers[category] = (
                AutoTokenizer.from_pretrained(model_path)
            )
            PredictSentimen._models[category].eval()
            logger.success(f"[{category.upper()}] Model & tokenizer berhasil dimuat")
        else:
            logger.debug(f"[{category.upper()}] Model sudah dimuat, skip loading")

        self.model     = PredictSentimen._models[category]
        self.tokenizer = PredictSentimen._tokenizers[category]

    def _tokenize(self, text):
        return self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=self.max_length,
        )

    def predict(self, text: str) -> str:
        inputs = self._tokenize(text)
        with torch.no_grad():
            outputs = self.model(**inputs)
        pred = outputs.logits.argmax(1).item()
        return self.label_map[pred]

    def predict_with_score(self, text: str) -> dict:
        inputs = self._tokenize(text)
        with torch.no_grad():
            outputs = self.model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)[0]
        pred  = probs.argmax().item()
        return {
            "label":      self.label_map[pred],
            "confidence": round(probs[pred].item(), 4),
        }

    def predict_batch(self, texts: list[str]) -> list[str]:
        inputs = self._tokenize(texts)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return [self.label_map[p] for p in outputs.logits.argmax(1).tolist()]
