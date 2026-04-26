import json
import re
from typing import List, Dict, Tuple
import os
import unicodedata

from nft_shared.config.config import anagram, LOGO_EQUIV


def normalize_value(value: str):
    return unicodedata.normalize("NFKC", value).replace('С','C')


def normalize_logo(value: str) -> str:
    """Нормализуем известные логотипы"""
    return LOGO_EQUIV.get(value, value)


def calculate_sticker_synergy_value(attributes: List[dict], synergy_data: dict) -> Tuple[int, dict]:
    excluded_traits = set(synergy_data.get("traits", set()))
    synergy_keywords = set(synergy_data.get("keywords", set()))
    synergy_bonus_table = synergy_data.get("bonus_table", dict())

    synergy_counter = {}
    for attribute in attributes:
        trait_type = attribute.get("traitType").replace("Earring", "Earrings")
        value = normalize_value(attribute.get("value"))

        for old, new in anagram.items():
            value = value.replace(old, new)
        value = value.lower()

        if trait_type not in excluded_traits:
            theme = extract_synergy_theme(value, synergy_keywords)
            if theme:
                for word in theme:
                    synergy_counter[word] = synergy_counter.get(word, 0) + 1
    return calculate_synergy_bonus(synergy_counter, synergy_bonus_table)


def calculate_attribute_value(trait_type: str, value: str, attribute_data: dict) -> int:

    trait_values = attribute_data.get(trait_type, {})
    if not trait_values:
        print("---------------------------------------------------------")
        print("Not found attribute {}".format(trait_type))
        print("---------------------------------------------------------")
        return 0

    attr = trait_values.get(value, 0)
    if not attr:
        print("---------------------------------------------------------")
        print("Not found value {} for attribute {}".format(attr, trait_type))
        print("---------------------------------------------------------")
        return 0
    return attr


def calculate_name_value(name: str, name_attributes: dict) -> int:
    name_value = 0
    if name_attributes:
        # Проверяем каждое ключевое слово из атрибутов имени
        for keyword, value in name_attributes.items():
            if keyword in name:
                name_value += value
    return name_value

def calculate_number_value(name: str, num_attributes: dict) -> tuple[int, list[str]]:
    name_value, num_features = 0, list()

    name_info = analyze_name(name)
    for keyword, value in name_info.items():
        if value[0]:
            name_value += num_attributes.get(keyword, {}).get(str(value[1]), 0)
            if str(value[1]) in num_attributes.get(keyword, {}):
                num_features.append(keyword)
    return name_value, num_features

def calculate_nft_value(
        attributes: List[Dict[str, str]],
        attribute_values: Dict[str, Dict[str, float]],
        nft_name: str
):
    """
    Рассчитывает суммарную ценность NFT на основе атрибутов и таблицы ценностей.
    Также проверяет атрибуты из имени NFT (например, "Common", "Epic" в имени).

    Args:
        attributes: Список атрибутов NFT в формате [{"traitType": "...", "value": "..."}]
        attribute_values: Словарь ценностей атрибутов в формате {trait_type: {value: attribute_value}}
        nft_name: Имя NFT для поиска атрибутов в имени

    Returns:
        Суммарная ценность NFT
    """
    synergy_data = attribute_values.get("synergy", {})

    # Обрабатываем обычные атрибуты
    attr_value = 0
    attribute_data = attribute_values.get("attribute", {})
    name_attributes = attribute_values.get("name", {})
    num_attributes = attribute_values.get("number", {})

    for attribute in attributes:
        trait_type = attribute.get("traitType")
        trait_type = "Earrings" if  trait_type == "Earring" else trait_type
        value = normalize_value(attribute.get("value"))
        attr = calculate_attribute_value(trait_type, value, attribute_data)
        attr_value += attr
    synergy_bonus, synergy_data = calculate_sticker_synergy_value(attributes, synergy_data)
    name_value = calculate_name_value(nft_name, name_attributes)
    num_value, num_features = calculate_number_value(nft_name, num_attributes)

    num_features = " ".join(num_features) if num_features else "нет"
    return attr_value, synergy_bonus, name_value + num_value, num_features

# =========================
# EXTRACT SYNERGY
# =========================

def extract_synergy_theme(value: str, synergy_keywords: set) -> list:
    """
    Возвращает тему синергии из value
    Пример: 'Cosmic Cocktail' -> 'Cosmic'
    """
    words = []
    for word in value.split():
        if word in synergy_keywords:
            words.append(word)
    return words


def calculate_synergy_bonus(counter: dict, synergy_bonus_table: dict) -> Tuple[int, dict]:
    if not counter:
        return 0, {}

    synergy_bonus = {}

    total = 0
    for key, value in counter.items():
        if value < 2:
            continue
        key = "3+" if value >= 3 else str(value)
        bonus = synergy_bonus_table.get(key, 0)
        synergy_bonus[key] = {"bonus": bonus, "count": value}
        total += bonus
    return total, synergy_bonus

# =========================
# EXTRACT NUMBER
# =========================

def extract_number(name: str):
    """
    Извлекает число после символа #
    Пример: 'Orc Capped #3309' -> '3309'
    """
    match = re.search(r"#(\d+)", name)
    return match.group(1) if match else None


def is_numeric(s: str) -> bool:
    return s is not None and s.isdigit()


def digits(s: str):
    return [int(d) for d in s]


# =========================
# CHECKS
# =========================

def is_palindrome(num: str):
    if not is_numeric(num) or is_all_digits_same(num)[0]:
        return False, 0

    result = num == num[::-1]
    return result, len(num) if result else 0


def is_increasing(num: str):
    if not is_numeric(num):
        return False, 0

    d = digits(num)
    result = all(d[i] + 1 == d[i + 1] for i in range(len(d) - 1))
    return result, len(num) if result else 0


def is_decreasing(num: str):
    if not is_numeric(num):
        return False, 0

    d = digits(num)
    result = all(d[i] - 1 == d[i + 1] for i in range(len(d) - 1))
    return result, len(num) if result else 0


def is_symmetric(num: str):
    """
    Симметричная последовательность:
    возрастающая + убывающая (12321)
    или убывающая + возрастающая (32123)
    """
    if not is_numeric(num) or len(num) < 3 or len(num) % 2 != 1:
        return False, 0

    d = digits(num)
    mid = len(d) // 2 + 1

    left = d[:mid]
    right = d[mid -1:]

    inc_then_dec = (
        all(left[i] + 1 == left[i + 1] for i in range(len(left) - 1)) and
        all(right[i] - 1 == right[i + 1] for i in range(len(right) - 1))
    )

    dec_then_inc = (
        all(left[i] - 1 == left[i + 1] for i in range(len(left) - 1)) and
        all(right[i] + 1 == right[i + 1] for i in range(len(right) - 1))
    )

    result = inc_then_dec or dec_then_inc
    return result, len(num) if result else 0


def is_alternating_two_digits(num: str):
    """
    Чередование двух цифр: ABABAB
    Примеры: 1212, 525252
    """
    if not is_numeric(num) or len(num) < 4:
        return False, 0

    a, b = num[0], num[1]
    if a == b:
        return False, 0

    for i, ch in enumerate(num):
        if ch != (a if i % 2 == 0 else b):
            return False, 0

    return True, len(num)

def is_less_than(num: str):
    if not is_numeric(num):
        return False, 0

    for chek in (10, 100):
        if chek > int(num):
            return True, chek
    return False, 0

def is_all_digits_same(num: str):
    """
    Проверяет, что все цифры одинаковые
    Примеры: 11, 222, 4444
    """
    if not is_numeric(num):
        return False, 0

    result = len(set(num)) == 1
    return result, len(num) if result else 0

def is_multiple_of_10(num: str):
    """
    Проверяет, что число кратно 100
    Примеры: 100, 1200, 3300
    """
    if not num or not num.isdigit() or num=='0':
        return False, 0
    num, count = int(num), 0
    while num % 10 ==0:
        num = num // 10
        count += 1
    return count, count

def analyze_name(name: str) -> dict:
    """
    Полный анализ имени
    """
    num = extract_number(name)

    return {
        "Палиндром": is_palindrome(num),
        "Возрастающая последовательность": is_increasing(num),
        "Убывающая последовательность": is_decreasing(num),
        "Симметричная последовательность": is_symmetric(num),
        "Чередование двух цифр": is_alternating_two_digits(num),
        "Кратно 10": is_multiple_of_10(num),
        "Меньше": is_less_than(num),
        "Повторяющаяся  цифра": is_all_digits_same(num),
    }


def get_attribute_values_for_collection(
        collection_address: str
) -> Dict[str, Dict[str, float]]:
    """
    Получает все ценности атрибутов для коллекции.
    Формат: {trait_type: {value: attribute_value}}
    """
    if not os.path.exists(f'{collection_address}.json'):
        return {}

    with open(f'{collection_address}.json', encoding='utf-8') as f:
        attribute_values = json.load(f)
        return attribute_values
