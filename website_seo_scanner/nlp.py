from typing import Final, Literal

import re

import nltk
import numpy as np
import polars as pl
from langchain_text_splitters import RecursiveCharacterTextSplitter
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.cluster import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .depends import embeddings

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
STOPWORDS: Final[list[str]] = list(set(stopwords.words("russian")))


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
        if token not in STOPWORDS and len(token) > MIN_TOKEN
    ]
    return " ".join(processed_tokens)


def _is_text_large(text: str) -> bool:
    return text > ...


def split_text(
        text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP
) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len
    )
    return splitter.split_text(text)


def compare_texts(
        text1: str,
        text2: str,
        similarity_strategy: Literal["max", "mean", "median", "std"] = "mean"
) -> float:
    """Сравнивает семантическую релевантность двух текстов"""
    chunks1, chunks2 = split_text(text1), split_text(text2)
    vectors = embeddings.embed_documents(chunks1 + chunks2)
    vectors1, vectors2 = vectors[:len(chunks1)], vectors[len(chunks1):]
    similarity_matrix = cosine_similarity(vectors1, vectors2)
    match similarity_strategy:
        case "max":
            similarity_score = np.max(similarity_matrix)
        case "mean":
            similarity_score = np.mean(similarity_matrix)
        case "median":
            similarity_score = np.median(similarity_matrix)
        case "std":
            similarity_score = np.std(similarity_matrix)
        case _:
            similarity_score = np.nan
    return float(similarity_score)


def extract_keywords(text: str, top_n: int = 10) -> list[str]:
    """Извлечение ключевых слов используя TF-IDF алгоритм.

    :param text: Входной текст.
    :param top_n: Количество возвращаемых ключевых слов.
    :return Список ключевых слов.
    """
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
    }).sort("scores", descending=True).head(top_n)["keywords"].to_list()


def extract_keyphrases(
        text: str, top_n: int = 5, ngram_range: tuple[int, int] = (5, 5)
) -> list[str]:
    """Извлечение ключевых фраз из текста.

    :param text: Входной текст.
    :param top_n: Количество возвращаемых ключевых фраз.
    :param ngram_range: Размер Н-граммы.
    :return Извлечённые ключевые фразы.
    """
    preprocessed_text = preprocess_text(text)
    count_vectorizer = CountVectorizer(ngram_range=ngram_range, stop_words=STOPWORDS)
    count_vectorizer.fit([preprocessed_text])
    candidates = count_vectorizer.get_feature_names_out()
    text_embedding = embeddings.embed_documents([text])
    candidate_embeddings = embeddings.embed_documents(candidates)
    distances = cosine_similarity(text_embedding, candidate_embeddings)
    return [candidates[index] for index in distances.argsort()[0][-top_n:]]


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
