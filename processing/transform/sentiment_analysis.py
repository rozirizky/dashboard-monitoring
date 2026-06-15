import logging

try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers/torch not installed. Run: pip install transformers torch")

logger = logging.getLogger(__name__)

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
    _models: dict = {}
    _tokenizers: dict = {}

    def __init__(self, category: str):
        category = category.lower().strip()
        if category not in CATEGORY_CONFIG:
            raise ValueError(
                f"Unknown category '{category}'. Options: {', '.join(CATEGORY_CONFIG)}"
            )

        self.category = category
        self.config = CATEGORY_CONFIG[category]
        self.label_map = self.config["label_map"]
        self.max_length = self.config["max_length"]
        self._load_model()

    def _load_model(self):
        cat = self.category
        path = self.config["model_path"]

        if cat not in PredictSentimen._models:
            logger.info("Loading model for '%s' from '%s'", cat, path)
            PredictSentimen._models[cat] = AutoModelForSequenceClassification.from_pretrained(path)
            PredictSentimen._tokenizers[cat] = AutoTokenizer.from_pretrained(path)
            PredictSentimen._models[cat].eval()
            logger.info("Model '%s' loaded successfully", cat)

        self.model = PredictSentimen._models[cat]
        self.tokenizer = PredictSentimen._tokenizers[cat]

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
        return self.label_map[outputs.logits.argmax(1).item()]

    def predict_with_score(self, text: str) -> dict:
        inputs = self._tokenize(text)
        with torch.no_grad():
            outputs = self.model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)[0]
        pred = probs.argmax().item()
        return {"label": self.label_map[pred], "confidence": round(probs[pred].item(), 4)}

    def predict_batch(self, texts: list[str]) -> list[str]:
        inputs = self._tokenize(texts)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return [self.label_map[p] for p in outputs.logits.argmax(1).tolist()]
