from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from website_seo_scanner.depends import embeddings
from website_seo_scanner.nlp import STOPWORDS

text = """В PyTorch переключение между режимами обучения и оценки критически важно для обеспечения корректного поведения модели во время обучения и вывода. Два важных метода, model.eval()и model.train(), управляют этим поведением. Давайте рассмотрим, что делает каждый метод и почему он важен.

model.train()
Это режим по умолчанию при создании модели PyTorch. Он сообщает модели, что она находится в режиме обучения. Некоторые слои ведут Dropoutсебя BatchNormпо-разному при обучении и оценке. Например:

Функция исключения случайным образом обнуляет некоторые элементы входного тензора во время обучения, чтобы предотвратить переобучение.
BatchNorm нормализует входные данные на основе статистики (среднего значения и дисперсии) текущего пакета.
model.eval()
После завершения обучения и необходимости оценить модель на проверочных или тестовых данных необходимо переключиться в режим оценки, используя model.eval(). Это отключает определённые функции, такие как отсев, и гарантирует, что слои пакетной нормализации будут использовать накопленную статистику, а не статистику, специфичную для конкретного пакета.

model.eval ()   # Перейти в режим оценки с помощью torch.no_grad ():   # Отключить расчет градиента     out_data = model(data)


Зачем использовать torch.no_grad()с model.eval()?
Хотя model.eval()это обеспечивает корректное поведение слоёв во время вывода, это не отключает вычисление градиентов. Чтобы избежать ненужного использования памяти и повысить производительность при оценке, следует использовать в паре model.eval()с torch.no_grad(). Это гарантирует, что градиенты не будут вычисляться для операций внутри блока.

Пример: переключение между обучением и оценкой

# Режим обучения
 model.train() 
# Ваш цикл обучения 
# ... 
# Теперь переключитесь в режим оценки для проверочной
 модели. eval () 

с torch.no_grad():   # Без вычисления градиента для оценки
     out_data = model(data) 

# Не забудьте переключиться обратно в режим обучения!
 model.train()
Заключение:
Используйте model.train()при обучении, чтобы такие слои, как исключение и пакетная нормализация, вели себя правильно.
Используйте model.eval()при оценке или тестировании, особенно если вы не оптимизируете модель.
Объедините model.eval()с torch.no_grad()во время оценки, чтобы отключить вычисление градиента и сэкономить память.
Надеюсь, это краткое объяснение с кодом прояснит разницу между этими двумя режимами!
"""

print(len(text))

vectorizer = CountVectorizer(ngram_range=(5, 5), stop_words=STOPWORDS)
vectorizer.fit([text])

candidates = vectorizer.get_feature_names_out()

print(candidates)

doc_embedding = embeddings.embed_documents([text])

candidate_embeddings = embeddings.embed_documents(candidates)

distances = cosine_similarity(doc_embedding, candidate_embeddings)

top_n = 5
keyphrases = [candidates[index] for index in distances.argsort()]

print(keyphrases)
