"""
filter_engine.py — логика фильтрации стикеров по атрибутным правилам.

Формат filter_json для типа 'attrs':
{
    "type": "attrs",
    "threshold_value_ratio": 1.5,       # опционально
    "filters": [
        ["Gold Ring", "Diamond"],        # group 1: AND — стикер должен иметь ОБА
        ["Happy", "Angry"]               # group 2: AND — стикер должен иметь ОДИН из... нет, AND
    ]
    # Между группами — OR: стикер попадает если выполняется хотя бы одна группа
}
"""
from typing import Any, Dict, List

from nft_shared.models.sticker import StickerORM


def _get_sticker_attr_values(sticker: StickerORM) -> set[str]:
    """Все значения атрибутов стикера в плоский set."""
    values = set()
    for attr in (sticker.attr1, sticker.attr2, sticker.attr3, sticker.attr4):
        if attr:
            values.add(attr.value)
    return values


def matches_attr_filter(sticker: StickerORM, filters: List[List[str]]) -> bool:
    """
    filters — список групп.
    Между группами: OR (достаточно одной).
    Внутри группы: AND (все атрибуты должны присутствовать).
    """
    sticker_values = _get_sticker_attr_values(sticker)
    for group in filters:
        if all(attr in sticker_values for attr in group):
            return True
    return False


def matches_rule(sticker: StickerORM, nft_price: float, rule: Dict[str, Any]) -> bool:
    """
    Проверяет одно правило мониторинга.

    rule_type:
    - 'min_price': price <= threshold
    - 'value_ratio': price / total_value <= threshold (чем ниже — тем выгоднее)
    - 'attrs': attr filter + опциональный value_ratio
    """
    rule_type = rule.get("type")
    filter_json = rule.get("filter_json", {})

    if rule_type == "min_price":
        threshold = filter_json.get("threshold_price", 0)
        return nft_price is not None and nft_price <= threshold

    elif rule_type == "value_ratio":
        threshold = filter_json.get("threshold_ratio", 1.0)
        if not nft_price or not sticker.total_value:
            return False
        ratio = nft_price / sticker.total_value
        return ratio <= threshold

    elif rule_type == "attrs":
        filters = filter_json.get("filters", [])
        if not matches_attr_filter(sticker, filters):
            return False
        # Опциональная проверка value_ratio
        threshold_ratio = filter_json.get("threshold_value_ratio")
        if threshold_ratio is not None:
            if not nft_price or not sticker.total_value:
                return False
            return (nft_price / sticker.total_value) <= threshold_ratio
        return True

    return False