from typing import Final, Literal

import re

import nltk
import numpy as np
import polars as pl
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from pydantic import BaseModel, Field
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity

from .depends import llm, nlp

nltk.download("stopwords")
nltk.download("wordnet")

RANDOM_STATE = 42
# Минимальное значение токена для пред обработки текста
MIN_TOKEN = 2
# Минимальная длина предложения для извлечения ключевых слов
MIN_SENTENCE_LENGTH = 10
# Промпт для извлечения ключевых слов используя LLM
KEYWORDS_EXTRACTION_PROMPT = """
"""
# Загрузка стоп-слов для русского языка (слова несущие малую смысловую нагрузку)
stopwords: Final[set[str]] = set(stopwords.words("russian"))


class KeywordsResponse(BaseModel):
    """Ответ LLM с извлечёнными ключевыми словами"""
    keywords: list[str] = Field(..., description="Ключевые слова на странице")


def compare_texts(text1: str, text2: str) -> float:
    """Сравнивает релевантность двух текстов"""
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]


def extract_keywords(
        text: str, strategy: Literal["llm", "ml", "tf-idf"] = "ml"
) -> list[str]:
    """Извлекает ключевые слова из текста.

    :param text: Текст для извлечения ключевых слов.
    :param strategy: Стратегия для извлечения: 'llm', 'ml', ...
    :return Список ключевых слов на странице.
    """
    match strategy:
        case "ml":
            document = nlp(text)
            return [
                token.text for token in document if token.pos_ in {"NOUN", "PROPN", "ADJ"}
            ]
        case "llm":
            parser = PydanticOutputParser(pydantic_object=KeywordsResponse)
            prompt = (
                ChatPromptTemplate
                .from_messages(["system", KEYWORDS_EXTRACTION_PROMPT])
                .partial(format_instructions=parser.get_format_instructions())
            )
            chain: RunnableSerializable[dict[str, str], KeywordsResponse] = prompt | llm | parser
            response = chain.invoke({"text": text})
            return response.keywords
        case "tf-idf":
            return ...


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


def calculate_cluster_entropy(cluster_center: np.ndarray[float]) -> float:
    """Расчет энтропии кластера для оценки его чистоты"""
    normalized_center = np.abs(cluster_center)
    if normalized_center.sum() == 0:
        return 0.0
    normalized_center /= normalized_center.sum()
    # Расчет энтропии Шеннона
    entropy = -np.sum(normalized_center * np.log2(normalized_center + 1e-10))
    return float(entropy)


def find_optimal_clusters(texts: list[str], max_features: int) -> int:
    """Поиск оптимального количества текстовых кластеров методом силуэта.

    :param texts: Тексты для кластеризации.
    :param max_features: Выборка первых N признаков на основе количества.
    :return Оптимальное число кластеров.
    """
    if len(texts) == 1:
        return 1
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        min_df=1,
        max_df=0.8,
        stop_words=None
    )
    tfidf_matrix = vectorizer.fit_transform(texts)
    # Метод локтя с силуэтным анализом
    max_possible = min(10, len(texts) - 1)
    best_score = -1
    best_k = 2
    for k in range(2, max_possible + 1):
        try:
            svd = TruncatedSVD(n_components=k)
            lsi_vectors = svd.fit_transform(tfidf_matrix)
            kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=5)
            clusters = kmeans.fit_predict(lsi_vectors)
            if len(np.unique(clusters)) > 1:
                score = silhouette_score(lsi_vectors, clusters)
                if score > best_score:
                    best_score = score
                    best_k = k
        except ValueError:
            continue
    return best_k


def get_semantic_clusters(
        texts: list[str], n_clusters: int = 5, max_features: int = 1000
) -> ...:
    """Получение смысловых кластеров в текстах

    :param texts: Тексты для семантического анализа.
    :param n_clusters: Количество кластеров.
    :param max_features: Максимальное количество признаков.
    :return ...
    """
    preprocessed_texts = [preprocess_text(text) for text in texts]
    # TF-IDF векторизация текста
    vectorizer = TfidfVectorizer(max_features=max_features, ngram_range=(1, 3))
    tfidf_matrix = vectorizer.fit_transform(preprocessed_texts)
    # LSI (Latent Semantic Indexing) с SVD
    svd = TruncatedSVD(n_components=n_clusters, random_state=RANDOM_STATE)
    lsi_vectors = svd.fit_transform(tfidf_matrix)
    # Кластеризация
    optimal_n_clusters = min(n_clusters, find_optimal_clusters(texts, max_features))
    kmeans = KMeans(n_clusters=optimal_n_clusters, random_state=RANDOM_STATE)
    clusters = kmeans.fit_predict(lsi_vectors)
    # Ключевые слова для каждого кластера
    cluster_keywords: dict[int, dict[str, list[str] | int]] = {}
    feature_names = vectorizer.get_feature_names_out()
    for cluster_id in range(n_clusters):
        cluster_indices = np.where(clusters == cluster_id)[0]
        if len(cluster_indices) > 0:
            # Средний вектор для кластера
            cluster_center = kmeans.cluster_centers_[cluster_id]
            # Наиболее важные признаки
            top_indices = cluster_center.argsort()[-10:][::-1]
            top_keywords = [feature_names[i] for i in top_indices]
            cluster_keywords[cluster_id] = {
                "keywords": top_keywords,
                "doc_count": len(cluster_indices)
            }
    return clusters, cluster_keywords


def build_lsi_graph(text: str) -> ...:
    ...
