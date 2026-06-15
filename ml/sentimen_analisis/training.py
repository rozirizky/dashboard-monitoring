import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from torch.optim import AdamW
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import logging
import time
import os
from datetime import datetime




def main():
    os.makedirs("logs", exist_ok=True)
    log_filename = f"logs/training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler()         
        ]
    )
    log = logging.getLogger(__name__)
    log.info(f"Log disimpan ke: {log_filename}")


    log.info("Memuat dataset...")
    df = pd.read_json("data/dataset_sentimen.json")
    df["labels"] = df["sentimen"].map({
        "Bearish": 0,
        "Bullish": 1,
        "Netral":  2
    })
    log.info(f"Dataset dimuat: {len(df)} baris | distribusi label:\n{df['sentimen'].value_counts().to_string()}")


    pairs_list     = df["pair"].unique().tolist()
    special_tokens = [f"<PAIR_{p}>" for p in pairs_list]

    log.info(f"Memuat tokenizer dari 'model/finbert'...")
    tokenizer = AutoTokenizer.from_pretrained("model/finbert", local_files_only=True)
    tokenizer.add_special_tokens({"additional_special_tokens": special_tokens})
    log.info(f"Special tokens ditambahkan: {special_tokens}")


    log.info("Memuat model FinBERT (num_labels=3)...")
    model = AutoModelForSequenceClassification.from_pretrained(
        "model/finbert",
        num_labels=3,
        local_files_only=True
    )
    model.resize_token_embeddings(len(tokenizer))


    assert len(tokenizer) == model.get_input_embeddings().weight.shape[0], \
        "Ukuran vocab tidak cocok!"
    log.info(f"Vocab size: {len(tokenizer)} ✓ | Device: cpu")


    def add_pair_context(texts, pairs):
        return [f"<PAIR_{p}> {t}" for t, p in zip(texts, pairs)]

    train_teks, test_teks, train_label, test_label, train_pair, test_pair = train_test_split(
        df["news"].tolist(), df["labels"].tolist(), df["pair"].tolist(),
        test_size=0.15, random_state=42, stratify=df["labels"]
    )
    train_teks, val_teks, train_label, val_label, train_pair, val_pair = train_test_split(
        train_teks, train_label, train_pair,
        test_size=0.15, random_state=42, stratify=train_label
    )

    train_teks = add_pair_context(train_teks, train_pair)
    val_teks   = add_pair_context(val_teks,   val_pair)
    test_teks  = add_pair_context(test_teks,  test_pair)

    log.info(f"Split data → Train: {len(train_teks)} | Val: {len(val_teks)} | Test: {len(test_teks)}")


    log.info("Tokenisasi data...")
    def tokenize(texts):
        return tokenizer(
            texts, padding=True, truncation=True,
            max_length=512, return_tensors="pt"
        )

    train_token = tokenize(train_teks)
    val_token   = tokenize(val_teks)
    test_token  = tokenize(test_teks)
    log.info("Tokenisasi selesai ✓")


    class ForexDataset(Dataset):
        def __init__(self, tokens, labels):
            self.tokens = tokens
            self.labels = labels

        def __getitem__(self, idx):
            item = {k: v[idx] for k, v in self.tokens.items()}
            item["labels"] = torch.tensor(self.labels[idx])
            return item

        def __len__(self):
            return len(self.labels)

    BATCH_SIZE   = 16
    train_loader = DataLoader(ForexDataset(train_token, train_label), batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = DataLoader(ForexDataset(val_token,   val_label),   batch_size=BATCH_SIZE)
    test_loader  = DataLoader(ForexDataset(test_token,  test_label),  batch_size=BATCH_SIZE)
    log.info(f"DataLoader siap | batch_size={BATCH_SIZE} | "
             f"train_batches={len(train_loader)} | val_batches={len(val_loader)} | test_batches={len(test_loader)}")


    EPOCHS       = 5
    WARMUP_RATIO = 0.1
    total_steps  = len(train_loader) * EPOCHS
    warmup_steps = int(total_steps * WARMUP_RATIO)

    optimizer = AdamW([
        {"params": model.base_model.parameters(), "lr": 2e-5, "weight_decay": 0.01},
        {"params": model.classifier.parameters(), "lr": 1e-3, "weight_decay": 0.0},
    ])
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps
    )
    log.info(f"Optimizer: AdamW | Epochs: {EPOCHS} | Total steps: {total_steps} | Warmup steps: {warmup_steps}")


    best_val_loss  = float("inf")
    train_history  = []          
    training_start = time.time()

    log.info("=" * 60)
    log.info("MULAI TRAINING")
    log.info("=" * 60)

    for epoch in range(EPOCHS):
        epoch_start = time.time()
        log.info(f"\n{'─'*40}")
        log.info(f"EPOCH {epoch+1}/{EPOCHS}")
        log.info(f"{'─'*40}")


        model.train()
        total_train_loss = 0
        log_interval     = max(1, len(train_loader) // 5)   

        for step, batch in enumerate(train_loader, start=1):
            batch = {k: v for k, v in batch.items()}
            optimizer.zero_grad()
            outputs = model(**batch)
            loss    = outputs.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_train_loss += loss.item()

            if step % log_interval == 0 or step == len(train_loader):
                avg_so_far = total_train_loss / step
                lr_now     = scheduler.get_last_lr()[0]
                elapsed    = time.time() - epoch_start
                log.info(
                    f"  [Step {step:>4}/{len(train_loader)}] "
                    f"loss={loss.item():.4f} | avg_loss={avg_so_far:.4f} | "
                    f"lr={lr_now:.2e} | elapsed={elapsed:.1f}s"
                )

        avg_train_loss = total_train_loss / len(train_loader)


        model.eval()
        total_val_loss = 0
        val_preds, val_labels_list = [], []

        with torch.no_grad():
            for batch in val_loader:
                batch  = {k: v for k, v in batch.items()}
                outputs = model(**batch)
                total_val_loss  += outputs.loss.item()
                val_preds       += outputs.logits.argmax(1).tolist()
                val_labels_list += batch["labels"].tolist()

        avg_val_loss = total_val_loss / len(val_loader)
        epoch_time   = time.time() - epoch_start


        val_correct  = sum(p == l for p, l in zip(val_preds, val_labels_list))
        val_accuracy = val_correct / len(val_labels_list) * 100

        log.info(f"\n  ▶ EPOCH {epoch+1} SUMMARY")
        log.info(f"    Train Loss : {avg_train_loss:.4f}")
        log.info(f"    Val   Loss : {avg_val_loss:.4f}")
        log.info(f"    Val   Acc  : {val_accuracy:.2f}%")
        log.info(f"    Waktu      : {epoch_time:.1f}s")

        train_history.append({
            "epoch":      epoch + 1,
            "train_loss": avg_train_loss,
            "val_loss":   avg_val_loss,
            "val_acc":    val_accuracy,
            "time_s":     epoch_time,
        })

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            model.save_pretrained("model/model_forex_sentiment")
            tokenizer.save_pretrained("model/model_forex_sentiment")
            log.info(f"    ✅ Model terbaik disimpan (val_loss={best_val_loss:.4f})")
        else:
            log.info(f"    ⚠️  Val loss tidak membaik (best={best_val_loss:.4f})")


    total_time = time.time() - training_start
    log.info("\n" + "=" * 60)
    log.info("RINGKASAN TRAINING")
    log.info("=" * 60)
    log.info(f"{'Epoch':<8} {'Train Loss':<13} {'Val Loss':<12} {'Val Acc':<11} {'Waktu'}")
    log.info("-" * 60)
    for h in train_history:
        log.info(
            f"{h['epoch']:<8} {h['train_loss']:<13.4f} {h['val_loss']:<12.4f} "
            f"{h['val_acc']:<11.2f} {h['time_s']:.1f}s"
        )
    log.info(f"\nTotal waktu training : {total_time/60:.1f} menit")
    log.info(f"Best val loss        : {best_val_loss:.4f}")


    log.info("\n" + "=" * 60)
    log.info("EVALUASI TEST SET")
    log.info("=" * 60)

    model = AutoModelForSequenceClassification.from_pretrained(
        "model/model_forex_sentiment",
        local_files_only=True
    )

    model.eval()
    log.info("Model terbaik dimuat untuk evaluasi test.")

    all_preds, all_labels = [], []
    with torch.no_grad():
        for batch in test_loader:
            batch      = {k: v for k, v in batch.items()}
            outputs    = model(**batch)
            all_preds  += outputs.logits.argmax(1).tolist()
            all_labels += batch["labels"].tolist()

    report = classification_report(
        all_labels, all_preds,
        target_names=["Bearish", "Bullish", "Netral"]
    )
    print(report)
    log.info("Classification Report:\n" + report)
    log.info(f"Log lengkap tersimpan di: {log_filename}")


if __name__ == "__main__":
    main()
