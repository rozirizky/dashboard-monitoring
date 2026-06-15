import re
import warnings

import nltk
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

warnings.filterwarnings("ignore")

for pkg in ["stopwords", "punkt", "punkt_tab"]:
    try:
        nltk.data.find(f"tokenizers/{pkg}" if "punkt" in pkg else f"corpora/{pkg}")
    except LookupError:
        nltk.download(pkg, quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

STOPWORDS_EN = set(stopwords.words("english"))


def _clean(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"\$[\d,.]+", " ", text)
    text = re.sub(r"\b\d[\d,.]*\b", " ", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokenize(text: str) -> list[str]:
    return [t for t in word_tokenize(_clean(text)) if t not in STOPWORDS_EN and len(t) > 2]


def extract_keywords(
    content: str,
    title: str,
    top_n: int = 10,
    title_weight: float = 2.0,
) -> list[dict]:
    full_text = f"{' '.join([title] * int(title_weight))} {content}"

    vectorizer = TfidfVectorizer(
        tokenizer=_tokenize,
        stop_words=list(STOPWORDS_EN),
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
        token_pattern=None,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([full_text])
    except ValueError:
        return []

    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]
    results = [
        {"keyword": feat, "score": round(float(score), 4)}
        for feat, score in zip(feature_names, scores)
        if score > 0
    ]
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


def summarize(
    content: str,
    title: str,
    num_sentences: int = 3,
) -> str:
    sentences = sent_tokenize(content)
    if len(sentences) <= num_sentences:
        return content.strip()

    vectorizer = TfidfVectorizer(
        tokenizer=_tokenize,
        stop_words=list(STOPWORDS_EN),
        min_df=1,
        token_pattern=None,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([title] + sentences)
    except ValueError:
        return sentences[0]

    title_vec = tfidf_matrix[0]
    sentence_vecs = tfidf_matrix[1:]
    title_sim = cosine_similarity(title_vec, sentence_vecs)[0]

    sim_matrix = cosine_similarity(sentence_vecs)
    np.fill_diagonal(sim_matrix, 0)
    inter_scores = sim_matrix.sum(axis=1) / (len(sentences) - 1 + 1e-9)
    final_scores = 0.6 * inter_scores + 0.4 * title_sim

    top_indices = sorted(np.argsort(final_scores)[::-1][:num_sentences])
    return " ".join(sentences[i] for i in top_indices).strip()


def process_article(
    title: str,
    content: str,
    top_n_keywords: int = 10,
    num_summary_sentences: int = 3,
) -> dict:
    keywords = extract_keywords(content, title, top_n=top_n_keywords)
    summary = summarize(content, title, num_sentences=num_summary_sentences)
    return {
        "tags": [k["keyword"] for k in keywords],
        "keywords": keywords,
        "summary": summary,
    }
