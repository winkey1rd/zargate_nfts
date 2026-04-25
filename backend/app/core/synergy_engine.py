"""
New synergy engine with database-first approach.
Implements the complete synergy logic from requirements.
"""
from typing import Dict, List, Tuple
from collections import defaultdict
from transfer_app.db.models import Sticker, Wallet
from transfer_app.db.repositories import StickerRepository
from transfer_app.config.config import ATTRIBUTE_GROUPS, EMOTION_ORDER
import logging

logger = logging.getLogger(__name__)


def _build_synergy_row(remaining_stickers: Dict[int, Sticker],
                       group_name: str,
                       wallet_priority: str = None,
                       attr_value: str = None) -> Dict:
    """
    Build one row of synergy - UNIQUE EMOTIONS (one sticker per emotion).

    Algorithm:
    1. Group remaining stickers by emotion
    2. For EACH emotion, select ONE BEST sticker (highest value) across ALL wallets
    3. Prioritize priority wallet if it has a candidate for that emotion
    4. Result: row has unique emotions, no duplicates even across wallets
    5. Return sticker with its own wallet info preserved
    """
    stickers = list(remaining_stickers.values())

    if not stickers:
        return {'emotions': {}}

    # Group by emotion
    by_emotion = defaultdict(list)
    for sticker in stickers:
        by_emotion[sticker.emotion].append(sticker)

    # For each emotion, select ONE best sticker globally (unique emotions)
    row_emotions = {}
    for emotion, emotion_stickers in by_emotion.items():
        # Prioritize: if priority wallet has this emotion, pick best sticker from priority
        # Otherwise, pick global best
        best_sticker = None

        if wallet_priority:
            priority_candidates = [
                s for s in emotion_stickers
                if s.wallet and s.wallet.address == wallet_priority
            ]
            if priority_candidates:
                best_sticker = max(priority_candidates, key=lambda s: s.total_value)

        # If no priority candidate found, pick globally best
        if not best_sticker:
            best_sticker = max(emotion_stickers, key=lambda s: s.total_value)

        # Store in wallets dict keyed by wallet address
        wallet_addr = best_sticker.wallet.address if best_sticker.wallet else "unknown"
        emotion_data = {'wallets': {wallet_addr: best_sticker}, 'count': 0}

        # Count attribute matches. If attr_value specified, count only
        # attributes in this group whose value equals attr_value. Otherwise
        # fall back to counting all attribute entries in the group.
        attr_values = best_sticker.get_attribute_values_for_group(group_name) or []
        if attr_value is not None:
            # attr_values may be list of values; count exact matches
            if group_name == "Logos":
                emotion_data['count'] = sum(1 for v in attr_values if v == attr_value)
            # ensure at least 1 (sticker contributed the attribute)
            if emotion_data['count'] == 0:
                emotion_data['count'] = 1
        else:
            emotion_data['count'] = len(attr_values) if attr_values else 1

        row_emotions[emotion] = emotion_data

    # compute total attribute count for this row (sum of per-emotion counts)
    row_attr_count = sum(info.get('count', 0) for info in row_emotions.values())
    return {
        'emotions': row_emotions,
        'total_in_row': len(row_emotions),
        'row_attr_count': row_attr_count
    }

def _calculate_synergy_for_value(attr_value: str,
                                 stickers: List[Sticker],
                                 group_name: str,
                                 wallet_priority: str = None) -> Dict:
    """
    Calculate synergy for a specific attribute value.
    Builds multiple rows as needed.

    count = number of attributes this sticker has in this group
    total_count = TOTAL stickers with this attribute
    max_row_count = maximum stickers in any single row (what we display as "count")
    """
    # Track which stickers we've used
    remaining_stickers = {s.id: s for s in stickers}
    rows = []
    row_num = 0
    max_row_stickers = 0  # Track max stickers in any row

    # Build rows until we run out of stickers
    while remaining_stickers and row_num < 20:
        # pass attr_value through so row builder can count only matches
        row_data = _build_synergy_row(
            remaining_stickers,
            group_name,
            wallet_priority,
            attr_value=attr_value
        )

        if not row_data['emotions']:
            break

        rows.append(row_data)

        # row_data may supply its own attr count
        row_attr_count = row_data.get('row_attr_count')
        if row_attr_count is None:
            row_attr_count = sum(info.get('count', 0) for info in row_data['emotions'].values())
        max_row_stickers = max(max_row_stickers, row_attr_count)

        # Remove used stickers from remaining
        for emotion_info in row_data['emotions'].values():
            for sticker in emotion_info['wallets'].values():
                if isinstance(sticker, Sticker):
                    remaining_stickers.pop(sticker.id, None)

        row_num += 1

    return {
        'total_count': len(stickers),  # Total stickers with this attribute
        'max_row_count': max_row_stickers,  # Max stickers in any single row (display as count)
        'rows': rows,
        'remaining': len(remaining_stickers)
    }

class SynergyEngine:
    def _sticker_power(self, s: Sticker) -> float:
        """Return the raw power/value of a sticker."""
        return getattr(s, "total_value", 0) or 0

    def _build_strong_team(self, remaining_list: List[Sticker], team_size: int) -> Tuple[List[Sticker], float]:
        """Return strongest-by-emotion team and its power (includes 350 bonus).

        This helper is used as a fallback on the first iteration or when no
        valid synergies are found. Separated into its own method so it can be
        patched and tested.
        """
        team: List[Sticker] = []
        for emo in EMOTION_ORDER:
            emo_candidates = [s for s in remaining_list if s.emotion == emo]
            if emo_candidates:
                team.append(max(emo_candidates, key=self._sticker_power))
            if len(team) >= team_size:
                break
        power = sum(self._sticker_power(s) for s in team)
        if len(team) >= team_size:
            power += 350
        return team, power

    def build_optimal_team(self, stickers: List[Sticker], team_size: int = 7) -> List[List[Sticker]]:
        """
        Build optimal teams using the exact 10‑step algorithm described by the user.

        Returns
        -------
        List[List[Sticker]]
            A list of teams. Each team is a list of Sticker objects (may be smaller
            than ``team_size`` for the last incomplete team).

        Algorithm (translated verbatim):
        1. Начинаем с полного набора стикеров выбранной окраски (фильтр по цвету
           вводится извне).
        2. По оставшимся стикерам ищем «синергии» — группы стикеров, которые
           делят одно значение атрибута.  У каждого стикера может быть несколько
           совпадающих атрибутов, поэтому в силу идёт **суммарное количество
           атрибутов**, а не число стикеров.  Игнорируем группы с менее чем четырьмя
           атрибутными очками.
        3. Для каждой найденной синергии вычисляем оценку: сумма power всех
           стикеров плюс бонус, пропорциональный количеству атрибутов.  Выбираем
           синергию с наивысшей оценкой.
        4. Берём стикеры из выбранной синергии и добираем отсутствующие эмоции
           самыми мощными стикерами той же кожи.
        5. Вычисляем суммарную силу команды (power + бонус).
        6. Параллельно строим альтернативную команду, просто беря самый сильный
           стикер каждой эмоции; если эмоций меньше семи, добавляем оставшиеся
           сильнейшие стикеры.
        7. Сравниваем две кандидата: команда со синергией остаётся только если её
           бонус превышает разницу по power; иначе выбираем вторую.
        8. Добавляем выбранную команду к результатам и исключаем её стикеры из
           рабочего набора.
        9. Повторяем шаги 2‑8 до исчерпания стикеров.
        10. Возвращаем список построенных команд.
        """
        if not stickers:
            return []

        remaining = list(stickers)
        teams: List[List[Sticker]] = []

        remaining = list(stickers)
        teams: List[List[Sticker]] = []

        # The algorithm loops until we exhaust the pool of stickers
        first_iteration = True
        while len(remaining) >= 1:
            # compute strong fallback team only on the first iteration; if later
            # we need it (no synergies found) we will compute lazily below
            chosen: List[Sticker] = []
            chosen_power: float = 0
            strong_team, strong_power = ([], 0)
            if first_iteration:
                strong_team, strong_power = self._build_strong_team(remaining, team_size)
                chosen, chosen_power = strong_team, strong_power

            synergy_bonus_table = {1:0,2:0,3:0,4:400,5:500,6:700,7:1000}

            # gather all potential synergies with attr_count>=4, then sort them
            synergies = []  # list of (group_name, attr_count, row)
            for group_name, traits in ATTRIBUTE_GROUPS.items():
                value_map = self._group_by_attribute_value(remaining, group_name)
                for value, stickers_with_value in value_map.items():
                    sy_data = _calculate_synergy_for_value(value, stickers_with_value, group_name)
                    for row in sy_data.get('rows', []):
                        attr_count = sum(info.get('count', 0) for info in row['emotions'].values())
                        if attr_count >= 4:
                            synergies.append((group_name, attr_count, row))
            # sort by attr_count descending
            synergies.sort(key=lambda tup: tup[1], reverse=True)

            # precompute addresses present in any synergy row, grouped by attribute group
            from collections import defaultdict
            all_synergy_ids_by_group = defaultdict(set)
            for grp, _, row in synergies:
                for info in row['emotions'].values():
                    for s in info['wallets'].values():
                        all_synergy_ids_by_group[grp].add(getattr(s, 'address', None))

            # iterate through sorted synergies
            for (group_name, attr_count, row) in synergies:
                # addresses to exclude: other stickers from same group
                current_ids = {getattr(s, 'address', None)
                               for info in row['emotions'].values()
                               for s in info['wallets'].values()}
                excluded_ids = all_synergy_ids_by_group[group_name] - current_ids

                # base synergy stickers from the row (one per emotion)
                synergy_stickers = [list(info['wallets'].values())[0] for info in row['emotions'].values()]

                # 3. Дополняем отсутствующие эмоции самыми сильными (из remaining, кроме уже взятых)
                candidate = list(synergy_stickers)
                present_emotions = {s.emotion for s in candidate}
                for emo in EMOTION_ORDER:
                    if emo not in present_emotions:
                        # exclude stickers that participate in any other synergy
                        candidates = [s for s in remaining if s.emotion == emo and s not in candidate and s.address not in excluded_ids]
                        if candidates:
                            candidate.append(max(candidates, key=self._sticker_power))

                bonus = synergy_bonus_table.get(attr_count, 0)
                candidate_power = sum(self._sticker_power(s) for s in candidate) + bonus
                # full-team bonus
                if len(candidate) >= team_size:
                    candidate_power += 350

                # 4. Сравниваем: если candidate_power больше, то это теперь лучшая команда
                if candidate_power > chosen_power:
                    chosen = candidate
                    chosen_power = candidate_power

            # if no synergies at all, fall back to strongest team
            if not synergies:
                if not strong_team:
                    strong_team, strong_power = self._build_strong_team(remaining, team_size)
                chosen = strong_team
                chosen_power = strong_power

            # 5. Добавляем лучшую найденную команду и исключаем её стикеры
            if chosen:
                teams.append(chosen)
                used = {s.address for s in chosen}
                remaining = [s for s in remaining if s.address not in used]
            else:
                # Если остались стикеры, которые не попали ни в одну команду (например, 1-6 штук), формируем из них отдельные команды по одному
                for s in remaining:
                    teams.append([s])
                remaining = []
                break

            first_iteration = False

        return teams

        # Обновлённый алгоритм построения команды:
        # 1. Собираем все стикеры, работа ведётся по оставшемуся набору.
        # 2. Для каждого атрибутного поля ищем возможные строки синергии и
        #    учитываем только те, у которых суммарный счёт атрибутов >= 4.
        # 3. Формируем перечень всех найденных синергий вместе с названиями
        #    групп и сортируем его по убыванию счёта (attr_count).
        # 4. Перед перебором вычисляем множества адресов, участвующих в любой
        #    синергии, отдельно для каждой группы.
        # 5. Идём по отсортированному списку. Для выбранной строки считаем, какие
        #    стикеры входят в остальные строки той же группы — эти адреса
        #    исключаем при доборе других эмоций, чтобы не ломать вторую синергию.
        #    Однако стикеры из синергий других групп допускаются, поскольку команда
        #    может содержать несколько синергий одновременно.
        # 6. Внутри текущей строки выбираем базовые стикеры (по эмоциям) и добираем
        #    отсутствующие эмоции самыми сильными оставшимися, не запрещёнными
        #    адресами. Если команды не хватает до team_size, докладываем сверху
        #    по той же логике с учётом исключений.
        # 7. Вычисляем мощность кандидата (сумма power + бонусы: за атрибуты и за
        #    полный состав). Сравниваем с лучшим найденным ранее и сохраняем
        #    при улучшении.
        # 8. Если в текущем наборе не было ни одной синергии, формируем по
        #    умолчанию команду «самых сильных эмоций».
        # 9. Добавляем выбранную команду к результатам, удаляем её стикеры из
        #    оставшегося набора и повторяем цикл.
        #10. Возвращаем список всех построенных команд.
    
    def __init__(self, sticker_repo: StickerRepository):
        self.repo = sticker_repo
        self.attribute_groups = ATTRIBUTE_GROUPS
    
    def build_synergies(self, 
                       group_name: str,
                       skin_tone: str,
                       wallet_priority: str = None) -> Dict:
        """
        Build synergies for a specific attribute group and skin tone.
        
        Args:
            group_name: Attribute group name (e.g., "Earrings", "Logos")
            skin_tone: Skin tone filter
            wallet_priority: Optional wallet address - its stickers appear first in each row
        
        Returns:
            Synergies organized by attribute value and rows
        """
        # Step 1: Get ALL stickers (no wallet filter - wallet is priority, not filter)
        all_stickers = self._get_stickers_for_query(skin_tone)
        
        if not all_stickers:
            logger.warning(f"No stickers found for {group_name}, {skin_tone}")
            return {}
        
        # Step 2: Group by attribute value
        value_stickers_map = self._group_by_attribute_value(all_stickers, group_name)
        
        if not value_stickers_map:
            return {}
        
        # Step 3: For each attribute value, build synergy rows
        results = {}
        for attr_value, stickers_with_value in value_stickers_map.items():
            synergy_data = _calculate_synergy_for_value(
                attr_value, 
                stickers_with_value,
                group_name,
                wallet_priority
            )
            results[attr_value] = synergy_data
        
        # Step 4: Sort by max_row_count (max stickers in any single row)
        sorted_results = dict(sorted(
            results.items(),
            key=lambda x: x[1]['max_row_count'],
            reverse=True
        ))
        
        return sorted_results
    
    def _get_stickers_for_query(self, skin_tone: str) -> List[Sticker]:
        """Get stickers matching skin tone (no wallet filtering).

        skin_tone may be None or the special string "ALL" to indicate no filter.
        """
        session = self.repo.session
        if not skin_tone or skin_tone == "ALL":
            return session.query(Sticker).all()
        return session.query(Sticker).filter(Sticker.skin_tone == skin_tone).all()
    
    def _group_by_attribute_value(self, 
                                 stickers: List[Sticker], 
                                 group_name: str) -> Dict[str, List[Sticker]]:
        """Group stickers by attribute value for a group."""
        result = defaultdict(list)
        
        for sticker in stickers:
            values = sticker.get_attribute_values_for_group(group_name)
            for value in values:
                result[value].append(sticker)
        
        return dict(result)

    
    def get_best_sticker_for_emotion_and_value(self,
                                              emotion: str,
                                              attr_value: str,
                                              group_name: str,
                                              wallet_address: str = None) -> Sticker:
        """
        Get single best sticker for emotion-value combination.
        Optionally filter by wallet.
        """
        all_stickers = self.repo.session.query(Sticker).all()
        
        # Filter by attribute value
        stickers = []
        for sticker in all_stickers:
            if sticker.has_attribute_value(group_name, attr_value):
                stickers.append(sticker)
        
        # Filter by emotion
        stickers = [s for s in stickers if s.emotion == emotion]
        
        if wallet_address:
            stickers = [s for s in stickers if s.wallet and s.wallet.address == wallet_address]
        
        if not stickers:
            return None
        
        # Return highest value
        return max(stickers, key=lambda s: s.total_value)

