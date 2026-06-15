
import re
import math
import warnings
from collections import Counter

import nltk
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

warnings.filterwarnings("ignore")

for pkg in ["stopwords", "punkt", "punkt_tab"]:
    try:
        nltk.data.find(f"tokenizers/{pkg}" if "punkt" in pkg else f"corpora/{pkg}")
    except LookupError:
        nltk.download(pkg, quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize


STOPWORDS_EN = set(stopwords.words("english"))

def clean_text(text: str) -> str:

    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)          
    text = re.sub(r"\$[\d,\.]+", " ", text)              
    text = re.sub(r"\b\d[\d,\.]*\b", " ", text)                               
    text = re.sub(r"[^a-zA-Z\s]", " ", text)             
    text = re.sub(r"\s+", " ", text).strip()
    return text



def tokenize(text: str) -> list[str]:

    tokens = word_tokenize(clean_text(text))
    return [t for t in tokens if t not in STOPWORDS_EN and len(t) > 2]

def extract_keywords(
    title: str,
    content: str,
    top_n: int = 10,
    title_weight: float = 2.0,
) -> list[dict]:
    
    title_repeat = " ".join([title] * int(title_weight))
    full_text = f"{title_repeat} {content}"

 
    vectorizer = TfidfVectorizer(
        tokenizer=tokenize,
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

    keyword_scores = [
        {"keyword": feat, "score": round(float(score), 4)}
        for feat, score in zip(feature_names, scores)
        if score > 0
    ]

    keyword_scores.sort(key=lambda x: x["score"], reverse=True)
    return keyword_scores[:top_n]


def summarize(
    title: str,
    content: str,
    num_sentences: int = 3,
) -> str:
  
    sentences = sent_tokenize(content)
    if len(sentences) <= num_sentences:
        return content.strip()

    all_texts = [title] + sentences
    vectorizer = TfidfVectorizer(
        tokenizer=tokenize,
        stop_words=list(STOPWORDS_EN),
        min_df=1,
        token_pattern=None,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(all_texts)
    except ValueError:
        return sentences[0]

  
    title_vec = tfidf_matrix[0]
    sentence_vecs = tfidf_matrix[1:]
    title_sim = cosine_similarity(title_vec, sentence_vecs)[0]


    sim_matrix = cosine_similarity(sentence_vecs)
    np.fill_diagonal(sim_matrix, 0)


    inter_scores = sim_matrix.sum(axis=1) / (len(sentences) - 1 + 1e-9)
    final_scores = 0.6 * inter_scores + 0.4 * title_sim


    top_indices = sorted(
        np.argsort(final_scores)[::-1][:num_sentences]
    )
    summary = " ".join([sentences[i] for i in top_indices])
    return summary.strip()



def process_article(
    title: str,
    content: str,
    top_n_keywords: int = 10,
    num_summary_sentences: int = 3,
) -> dict:
 
    keywords = extract_keywords(title, content, top_n=top_n_keywords)
    summary  = summarize(title, content, num_sentences=num_summary_sentences)

    return {
        "tags":     [k["keyword"] for k in keywords],
        "keywords": keywords,
        "summary":  summary,
    }



