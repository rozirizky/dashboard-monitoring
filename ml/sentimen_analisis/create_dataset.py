try:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
except ImportError:
    raise ImportError("Jalankan: pip install transformers")


def main():
    model_name = "ElKulako/cryptobert"
    print(f"Mengunduh model '{model_name}'...")

    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model.save_pretrained("model/model_crypto_sentiment")
    tokenizer.save_pretrained("model/model_crypto_sentiment")
    print("Model tersimpan ke model/model_crypto_sentiment")


if __name__ == "__main__":
    main()
