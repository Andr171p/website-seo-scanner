from typing import Final

import re

import nltk
import numpy as np
import polars as pl
from langchain_text_splitters import RecursiveCharacterTextSplitter
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.cluster import HDBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .depends import embeddings, nlp

nltk.download("stopwords")
nltk.download("wordnet")

CHUNK_SIZE, CHUNK_OVERLAP = 1024, 10
# Минимальное число кластеров
MIN_CLUSTER_SIZE = 2
# Ключевая метрика для кластеризации
HDBSCAN_METRIC = "euclidian"

RANDOM_STATE = 42
# Минимальное значение токена для пред обработки текста
MIN_TOKEN = 2
# Минимальная длина предложения для извлечения ключевых слов
MIN_SENTENCE_LENGTH = 10
# Загрузка стоп-слов для русского языка (слова несущие малую смысловую нагрузку)
stopwords: Final[set[str]] = set(stopwords.words("russian"))


def split_sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in text.split(".")
        if len(sentence.strip()) > MIN_SENTENCE_LENGTH
    ]


def split_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    return splitter.split_text(text)


def compare_texts(text1: str, text2: str) -> float:
    """Сравнивает релевантность двух текстов"""
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]


def get_semantic_similarity(text1: str, text2: str) -> float:
    """Рассчитывает семантическую близость двух текстов"""
    vectors = [text1, text2]
    return cosine_similarity(**vectors)[0][0]


def extract_keywords(text: str) -> list[str]:
    """Извлекает ключевые слова из текста.

    :param text: Текст для извлечения ключевых слов.
    :return Список ключевых слов на странице.
    """
    document = nlp(text)
    return [
        token.text for token in document if token.pos_ in {"NOUN", "PROPN", "ADJ"}
    ]


def extract_keyphrases(text: str, top_k: int) -> list[str]:
    """Извлечение ключевых фраз из текста.

    :param text: Текст из которого нужно извлечь ключевые фразы.
    :param top_k: Количество получаемых ключевых фраз.
    :return Извлечённые ключевые фразы.
    """
    sentences = split_sentences(text)
    sentence_vectors = embeddings.embed_documents(sentences)
    mean_vector = np.mean(sentence_vectors, axis=0)
    similarities = cosine_similarity([mean_vector], sentence_vectors)[0]
    top_indices = np.argsort(similarities)[::-top_k][::-1]
    return [sentences[top_index] for top_index in top_indices]


def get_semantic_clusters(texts: list[str]) -> dict[int, list[str]]:
    """Получает семантические кластеры для текстов.
    Использует transformers для векторизации и HDBSCAN для кластеризации.

    :param texts: Тексты, которые нужно кластеризовать.
    :return Маппинг индекса кластера и сгруппированных текстов.
    (cluster -> list[texts])
    """
    vectors = embeddings.embed_documents(texts)
    hdbscan = HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=None,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    clusters = hdbscan.fit_predict(vectors)
    groups: dict[int, list[str]] = {}
    for _, (text, cluster) in enumerate(zip(texts, clusters, strict=False)):
        if cluster not in groups:
            groups[int(cluster)] = []
        groups[cluster].append(text)
    return groups


def extract_keywords_using_tfidf(text: str, top_n: int = 20) -> ...:
    """Извлечение ключевых слов используя TF-IDF алгоритм"""
    sentences = re.split(r"[.!?]", text)  # Создание корпуса текста
    # из его предложений
    sentences = [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) > MIN_SENTENCE_LENGTH
    ]
    processed_sentences = [preprocess_text(sentence) for sentence in sentences]
    vectorizer = TfidfVectorizer(max_features=top_n * 2, ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(processed_sentences)
    # Суммируем TF-IDF scores по всем документам
    features_scores = np.array(tfidf_matrix.sum(axis=0)).flatten()
    feature_names = vectorizer.get_feature_names_out()
    # Сортировка по убыванию важности
    return pl.DataFrame({
        "keywords": feature_names, "scores": features_scores
    }).sort("scores", descending=True).head(top_n)


def preprocess_text(text: str) -> str:
    """Предобработка текста: очистка, лемматизация, удаление стоп-слов.

    :param text: Текст для обработки.
    :return Пред обработанный текст.
    """
    lemmatizer = WordNetLemmatizer()
    text = text.lower()
    text = re.sub(r"[^а-яёa-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = word_tokenize(text)
    processed_tokens: list[str] = [
        lemmatizer.lemmatize(token)
        for token in tokens
        if token not in stopwords and len(token) > MIN_TOKEN
    ]
    return " ".join(processed_tokens)
