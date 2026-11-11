import re


def normalize_phone(value: str) -> str:
    """
    Приводит российский номер к каноническому виду +7XXXXXXXXXX.
    Допускает скобки, тире, пробелы.
    Возвращает '' если номер невалиден (нет кода страны / неверная длина).

    Примеры:
        "+7 (999) 123-45-67"  -> "+79991234567"
        "8-999-123-45-67"     -> "+79991234567"
        "8 (999) 123 45 67"   -> "+79991234567"
        "9991234567"          -> ""   (нет кода страны)
        "+7 999 123 45 67"    -> "+79991234567"
        "7 999 123 45 67"     -> "+79991234567"
    """
    if not value:
        return ""

    value = value.strip()
    has_plus = value.startswith("+")
    digits = re.sub(r"\D", "", value)

    if not digits:
        return ""

    # 11 цифр: либо 8XXXXXXXXXX, либо 7XXXXXXXXXX
    if len(digits) == 11:
        if digits[0] == "8":
            digits = "7" + digits[1:]
        elif digits[0] == "7":
            pass  # уже в нужном виде
        else:
            return ""  # код страны не 7/8 — не российский номер
        return "+" + digits

    # 12 цифр с ведущим '+': +7XXXXXXXXXX
    if has_plus and len(digits) == 12 and digits[0] == "7":
        return "+" + digits

    # Всё остальное — невалидно (10 цифр без кода, 12 без '+', и т.д.)
    return ""