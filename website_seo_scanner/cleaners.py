import re


def clean(text: str) -> str:
    return remove_server_code(text)


def remove_server_code(text: str) -> str:
    """Удаляет PHP массивы и серверный код из текста"""
    patterns = [
        # PHP массивы: Array( [key] => value )
        r"Array\s*\(\s*\[.*?\]\s*=>\s*[^)]+\)",
        # Отдельные элементы массивов: [KEY] => VALUE
        r"\[\w+\]\s*=>\s*[^\n\r]*",
        # Квадратные скобки с текстом: [TEXT], [LINK]
        r"\[[\w_]+\]",
        # PHP переменные: $variable
        r"\$[a-zA-Z_]\w*",
        # PHP методы: ->method
        r"->\s*\w+",
        # URL с utm-метками
        r"&utm_[^&\s]+",
        # Специальные символы
        r"\xa0",  # неразрывный пробел
    ]
    cleaned_text = text
    for pattern in patterns:
        cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
    return cleaned_text.strip()
