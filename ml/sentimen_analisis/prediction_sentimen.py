from loguru import logger

try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
except ImportError:
    raise ImportError("Jalankan: pip install transformers torch")


class PredictSentimen():
    _model = None
    _tokenizer = None

    def __init__(self):
        if PredictSentimen._model is None:
            logger.info("Model belum dimuat, memulai loading...")

            logger.debug("Loading model dari 'model/model_forex_sentiment'...")
            PredictSentimen._model = AutoModelForSequenceClassification.from_pretrained("model/model_forex_sentiment")

            logger.debug("Loading tokenizer...")
            PredictSentimen._tokenizer = AutoTokenizer.from_pretrained("model/model_forex_sentiment")
           
            PredictSentimen._model.eval()
            logger.success("Model, tokenizer, dan translator berhasil dimuat")
        else:
            logger.debug("Model sudah dimuat sebelumnya, skip loading")

        self.model = PredictSentimen._model
        self.tokenizer = PredictSentimen._tokenizer


    def predict(self ,text):
        logger.debug(f"Memulai prediksi | panjang teks: {len(text)} chars")


        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128
        )

        with torch.no_grad():
            outputs = self.model(**inputs)

        pred = outputs.logits.argmax(1).item()
        label_map = {0: "bearish", 1: "bullish", 2: "netral"}
        result = label_map[pred]

        logger.debug(f"Hasil prediksi: {result}")
        return result
