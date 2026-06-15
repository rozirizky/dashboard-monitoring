"""
Training: Stock News Sentiment Analysis
========================================
Dataset : takala/financial_phrasebank (HuggingFace)
Model   : ProsusAI/finbert
Labels  : positive (0) | negative (1) | neutral (2)

Cara pakai:
  # Pakai dataset online (auto-download):
  python train_stock_sentiment.py

  # Pakai dataset lokal:
  python train_stock_sentiment.py --data-local

  # Konfigurasi custom:
  python train_stock_sentiment.py --epochs 10 --batch-size 32 --agreement 75

  # Pakai model lokal:
  python train_stock_sentiment.py --model-path model/finbert

Konfigurasi agreement Financial PhraseBank:
  50  → 4846 sampel (>=50% annotator setuju)
  66  → 4217 sampel (>=66% annotator setuju)
  75  → 3453 sampel (>=75% annotator setuju)  ← default, balance & quality
  100 → 2264 sampel (100% annotator setuju, kualitas tertinggi)
"""

import os
import time
import logging
import argparse
from datetime import datetime

import torch
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    get_linear_schedule_with_warmup,
)


# ─────────────────────────────────────────────────────────────────────────────
# Argumen CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Stock Sentiment Training — FinBERT + Financial PhraseBank")
    p.add_argument("--model-path",  default="ProsusAI/finbert",     help="Path/ID model (default: ProsusAI/finbert)")
    p.add_argument("--output-dir",  default="model/stock_sentiment", help="Direktori simpan model terbaik")
    p.add_argument("--agreement",   type=int, default=75, choices=[50, 66, 75, 100],
                   help="Tingkat agreement annotator Financial PhraseBank (default: 75)")
    p.add_argument("--epochs",      type=int, default=5,   help="Jumlah epoch (default: 5)")
    p.add_argument("--batch-size",  type=int, default=16,  help="Batch size (default: 16)")
    p.add_argument("--max-len",     type=int, default=128, help="Max token length (default: 128)")
    p.add_argument("--lr-base",     type=float, default=2e-5, help="LR base model (default: 2e-5)")
    p.add_argument("--lr-head",     type=float, default=1e-3, help="LR classifier head (default: 1e-3)")
    p.add_argument("--warmup-ratio",type=float, default=0.1,  help="Warmup ratio (default: 0.1)")
    p.add_argument("--test-size",   type=float, default=0.15, help="Proporsi test set (default: 0.15)")
    p.add_argument("--val-size",    type=float, default=0.15, help="Proporsi val dari train (default: 0.15)")
    p.add_argument("--seed",        type=int, default=42,  help="Random seed (default: 42)")
    p.add_argument("--data-local",  action="store_true",   help="Pakai dataset lokal di data/phrasebank.csv")
    p.add_argument("--no-cuda",     action="store_true",   help="Paksa CPU")
    return p.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# Setup logging
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging(output_dir: str) -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/stock_training_{ts}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    log = logging.getLogger("stock_train")
    log.info(f"Log disimpan ke: {log_file}")
    return log


# ─────────────────────────────────────────────────────────────────────────────
# Load dataset Financial PhraseBank
# ─────────────────────────────────────────────────────────────────────────────

LABEL_MAP_STOCK = {"positive": 0, "negative": 1, "neutral": 2}
LABEL_NAMES_STOCK = ["positive", "negative", "neutral"]

AGREEMENT_CONFIG = {
    50:  "sentences_50agree",
    66:  "sentences_66agree",
    75:  "sentences_75agree",
    100: "sentences_allagree",
}

def load_phrasebank_online(agreement: int, log: logging.Logger) -> pd.DataFrame:
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("Install dengan: pip install datasets")

    config = AGREEMENT_CONFIG[agreement]
    log.info(f"Mengunduh Financial PhraseBank (config='{config}')...")

    ds = load_dataset(
        "takala/financial_phrasebank",
        config,
        trust_remote_code=True,
    )

    data = ds["train"]

    # ── Debug: cek tipe label ────────────────────────────────────────────────
    log.info(f"Features: {data.features}")
    log.info(f"Contoh label[0]: {data['label'][0]} | type: {type(data['label'][0])}")

    # ── Handle label: bisa string atau int tergantung versi datasets ─────────
    raw_labels = data["label"]
    sample = raw_labels[0]

    if isinstance(sample, str):
        # Label sudah string: "positive" / "negative" / "neutral"
        log.info("Label format: STRING")
        label_strs = raw_labels

    elif isinstance(sample, int):
        # Label integer → coba int2str, fallback ke hardcode mapping
        log.info("Label format: INT — mencoba konversi...")
        feature = data.features["label"]
        if hasattr(feature, "int2str"):
            label_strs = [feature.int2str(l) for l in raw_labels]
        elif hasattr(feature, "names"):
            # ClassLabel punya .names list
            label_strs = [feature.names[l] for l in raw_labels]
        else:
            # Hardcode fallback: urutan di repo takala = negative(0), neutral(1), positive(2)
            log.warning("Tidak bisa auto-detect label name, pakai hardcode mapping repo takala")
            INT_TO_STR = {0: "negative", 1: "neutral", 2: "positive"}
            label_strs = [INT_TO_STR[l] for l in raw_labels]
    else:
        raise ValueError(f"Tipe label tidak dikenali: {type(sample)} — value: {sample}")

    df = pd.DataFrame({
        "text":      data["sentence"],
        "label_str": label_strs,
    })
    df["label"] = df["label_str"].map(LABEL_MAP_STOCK)

    # Validasi — pastikan tidak ada NaN setelah mapping
    if df["label"].isna().any():
        unknown = df[df["label"].isna()]["label_str"].unique().tolist()
        raise ValueError(f"Label tidak dikenali di LABEL_MAP_STOCK: {unknown}")

    log.info(f"Dataset dimuat: {len(df)} baris")
    log.info(f"Distribusi label:\n{df['label_str'].value_counts().to_string()}")
    return dfZ


def load_phrasebank_local(log: logging.Logger) -> pd.DataFrame:
    """
    Load dari file lokal data/phrasebank.csv
    Format kolom: sentence, label (string: positive/negative/neutral)
    """
    path = "data/phrasebank.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"File lokal tidak ditemukan: {path}\n"
            "Simpan CSV dengan kolom 'sentence' dan 'label' (positive/negative/neutral)"
        )
    df = pd.read_csv(path)
    assert "sentence" in df.columns and "label" in df.columns, \
        "CSV harus punya kolom 'sentence' dan 'label'"
    df = df.rename(columns={"sentence": "text"})
    df["label"] = df["label"].map(LABEL_MAP_STOCK)
    log.info(f"Dataset lokal dimuat: {len(df)} baris dari {path}")
    log.info(f"Distribusi label:\n{df['label'].value_counts().to_string()}")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Dataset PyTorch
# ─────────────────────────────────────────────────────────────────────────────

class SentimentDataset(Dataset):
    def __init__(self, tokens: dict, labels: list):
        self.tokens = tokens
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.tokens.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


# ─────────────────────────────────────────────────────────────────────────────
# Training loop
# ─────────────────────────────────────────────────────────────────────────────

def train_epoch(model, loader, optimizer, scheduler, device, log, epoch, total_epochs):
    model.train()
    total_loss = 0
    log_interval = max(1, len(loader) // 5)
    start = time.time()

    for step, batch in enumerate(loader, start=1):
        batch = {k: v.to(device) for k, v in batch.items()}
        optimizer.zero_grad()
        outputs = model(**batch)
        loss = outputs.loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        total_loss += loss.item()

        if step % log_interval == 0 or step == len(loader):
            log.info(
                f"  [Epoch {epoch}/{total_epochs} | Step {step:>4}/{len(loader)}] "
                f"loss={loss.item():.4f} | avg={total_loss/step:.4f} | "
                f"lr={scheduler.get_last_lr()[0]:.2e} | {time.time()-start:.1f}s"
            )

    return total_loss / len(loader)


def eval_epoch(model, loader, device):
    model.eval()
    total_loss = 0
    preds, labels_list = [], []

    with torch.no_grad():
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            total_loss += outputs.loss.item()
            preds += outputs.logits.argmax(1).tolist()
            labels_list += batch["labels"].tolist()

    avg_loss = total_loss / len(loader)
    accuracy = sum(p == l for p, l in zip(preds, labels_list)) / len(labels_list) * 100
    return avg_loss, accuracy, preds, labels_list


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    log = setup_logging(args.output_dir)

    device = torch.device(
        "cuda" if torch.cuda.is_available() and not args.no_cuda
        else "mps" if torch.backends.mps.is_available() and not args.no_cuda
        else "cpu"
    )
    log.info(f"Device: {device}")
    log.info(f"Config: epochs={args.epochs} | batch={args.batch_size} | "
             f"max_len={args.max_len} | agreement={args.agreement}%")

    # ── 1. Load dataset ──────────────────────────────────────────────────────
    if args.data_local:
        df = load_phrasebank_local(log)
    else:
        df = load_phrasebank_online(args.agreement, log)

    # ── 2. Split ─────────────────────────────────────────────────────────────
    texts  = df["text"].tolist()
    labels = df["label"].tolist()

    train_x, test_x, train_y, test_y = train_test_split(
        texts, labels, test_size=args.test_size,
        random_state=args.seed, stratify=labels
    )
    train_x, val_x, train_y, val_y = train_test_split(
        train_x, train_y, test_size=args.val_size,
        random_state=args.seed, stratify=train_y
    )
    log.info(f"Split → Train: {len(train_x)} | Val: {len(val_x)} | Test: {len(test_x)}")

    # ── 3. Tokenizer + model ─────────────────────────────────────────────────
    local = os.path.isdir(args.model_path)
    log.info(f"Memuat tokenizer dari: {args.model_path} ({'lokal' if local else 'HuggingFace'})")
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_path, local_files_only=local
    )

    log.info(f"Memuat model dari: {args.model_path}")
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_path,
        num_labels=3,
        ignore_mismatched_sizes=True,
        local_files_only=local,
    )
    model.resize_token_embeddings(len(tokenizer))
    model.to(device)
    log.info(f"Vocab size: {len(tokenizer)} | Model params: {sum(p.numel() for p in model.parameters()):,}")

    # ── 4. Tokenisasi ────────────────────────────────────────────────────────
    log.info("Tokenisasi data...")
    def tokenize(texts):
        return tokenizer(
            texts, padding=True, truncation=True,
            max_length=args.max_len, return_tensors="pt"
        )

    train_tok = tokenize(train_x)
    val_tok   = tokenize(val_x)
    test_tok  = tokenize(test_x)
    log.info("Tokenisasi selesai ✓")

    # ── 5. DataLoader ────────────────────────────────────────────────────────
    train_loader = DataLoader(SentimentDataset(train_tok, train_y), batch_size=args.batch_size, shuffle=True)
    val_loader   = DataLoader(SentimentDataset(val_tok,   val_y),   batch_size=args.batch_size)
    test_loader  = DataLoader(SentimentDataset(test_tok,  test_y),  batch_size=args.batch_size)
    log.info(f"DataLoader → train: {len(train_loader)} batches | val: {len(val_loader)} | test: {len(test_loader)}")

    # ── 6. Optimizer + scheduler ─────────────────────────────────────────────
    total_steps  = len(train_loader) * args.epochs
    warmup_steps = int(total_steps * args.warmup_ratio)

    optimizer = AdamW([
        {"params": model.base_model.parameters(), "lr": args.lr_base,  "weight_decay": 0.01},
        {"params": model.classifier.parameters(), "lr": args.lr_head,  "weight_decay": 0.0},
    ])
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )
    log.info(f"AdamW: lr_base={args.lr_base} | lr_head={args.lr_head} | "
             f"total_steps={total_steps} | warmup={warmup_steps}")

    # ── 7. Training loop ─────────────────────────────────────────────────────
    best_val_loss = float("inf")
    history = []
    training_start = time.time()

    log.info("=" * 60)
    log.info("MULAI TRAINING — STOCK SENTIMENT (FinBERT + Financial PhraseBank)")
    log.info("=" * 60)

    for epoch in range(1, args.epochs + 1):
        log.info(f"\n{'─'*50}\nEPOCH {epoch}/{args.epochs}\n{'─'*50}")
        epoch_start = time.time()

        avg_train_loss = train_epoch(
            model, train_loader, optimizer, scheduler,
            device, log, epoch, args.epochs
        )
        avg_val_loss, val_acc, val_preds, val_labels = eval_epoch(model, val_loader, device)
        epoch_time = time.time() - epoch_start

        log.info(f"\n  ▶ EPOCH {epoch} SUMMARY")
        log.info(f"    Train Loss : {avg_train_loss:.4f}")
        log.info(f"    Val   Loss : {avg_val_loss:.4f}")
        log.info(f"    Val   Acc  : {val_acc:.2f}%")
        log.info(f"    Waktu      : {epoch_time:.1f}s")

        history.append({
            "epoch": epoch, "train_loss": avg_train_loss,
            "val_loss": avg_val_loss, "val_acc": val_acc, "time_s": epoch_time,
        })

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            model.save_pretrained(args.output_dir)
            tokenizer.save_pretrained(args.output_dir)
            log.info(f"    ✅ Model terbaik disimpan → {args.output_dir} (val_loss={best_val_loss:.4f})")
        else:
            log.info(f"    ⚠️  Val loss tidak membaik (best={best_val_loss:.4f})")

    # ── 8. Ringkasan training ─────────────────────────────────────────────────
    total_time = time.time() - training_start
    log.info("\n" + "=" * 60)
    log.info("RINGKASAN TRAINING — STOCK SENTIMENT")
    log.info("=" * 60)
    log.info(f"{'Epoch':<8} {'Train Loss':<13} {'Val Loss':<12} {'Val Acc':<11} {'Waktu'}")
    log.info("-" * 60)
    for h in history:
        log.info(f"{h['epoch']:<8} {h['train_loss']:<13.4f} {h['val_loss']:<12.4f} "
                 f"{h['val_acc']:<11.2f} {h['time_s']:.1f}s")
    log.info(f"\nTotal waktu : {total_time/60:.1f} menit | Best val loss: {best_val_loss:.4f}")

    # ── 9. Evaluasi test set ──────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("EVALUASI TEST SET — STOCK SENTIMENT")
    log.info("=" * 60)

    best_model = AutoModelForSequenceClassification.from_pretrained(
        args.output_dir, local_files_only=True
    ).to(device)
    _, test_acc, test_preds, test_labels = eval_epoch(best_model, test_loader, device)

    report = classification_report(test_labels, test_preds, target_names=LABEL_NAMES_STOCK)
    log.info(f"Test Accuracy: {test_acc:.2f}%")
    log.info("Classification Report:\n" + report)

    cm = confusion_matrix(test_labels, test_preds)
    log.info(f"Confusion Matrix ({' | '.join(LABEL_NAMES_STOCK)}):\n{cm}")

    print("\n" + "=" * 60)
    print("STOCK SENTIMENT — TEST RESULTS")
    print("=" * 60)
    print(f"Test Accuracy: {test_acc:.2f}%")
    print(report)


if __name__ == "__main__":
    main()