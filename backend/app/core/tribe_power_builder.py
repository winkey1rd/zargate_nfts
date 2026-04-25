"""
Tribe Power Maximization Algorithm - Implementation

Formulates optimal teams for a skin tone (tribe) by:
1. Discovering all possible synergies across attribute groups
2. Identifying conflicts (stickers participating in multiple synergies)
3. Resolving conflicts using global optimization (maximum weight matching)
4. Building teams that maximize total tribe power (not individual team power)

This differs from build_optimal_team which is greedy and iterative.
"""
from itertools import count, groupby
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
import logging

from transfer_app.core.synergy_engine import _calculate_synergy_for_value
from transfer_app.db.models import Sticker
from transfer_app.db.repositories import StickerRepository
from transfer_app.config import ATTRIBUTE_GROUPS, EMOTION_ORDER, SYNERGY_THRESHOLDS, BRACELET_EMOTIONS, LOGO_EMOTIONS

logger = logging.getLogger(__name__)


class TribePowerBuilder:

    def count_team_attr(self, team, group, attr_value):
        count = 0
        for s in team:
            if hasattr(s, 'get_attribute_values_for_group'):
                values = s.get_attribute_values_for_group(group)
                count += sum(1 for v in values if v == attr_value)
        return count

    def _count_synergy_bonus(self, team, synergy_map):
        """
        Считает бонусы за синергию для команды:
        - Для каждой синергии суммирует количество атрибутов с нужным значением и группой у всех стикеров команды
        - Если сумма >= threshold, бонус определяется по self.synergy_bonus_table[count]
        """
        if isinstance(team, dict):
            team = list(team.values())
        total = 0
        for group, syn in synergy_map.items():
            attr_value = syn["attr_value"]
            threshold = self.synergy_thresholds.get(group, 4)
            count = self.count_team_attr(team, group, attr_value)
            if count >= threshold:
                bonus = self.synergy_bonus_table.get(count, 0)
                total += bonus
        return total

    def add_group_synergy(self, team, group, synergy_map, emotions, sticker_synergy_count):
        group_syn = synergy_map.get(group)
        group_added = set()
        if group_syn:
            source_stickers = group_syn.get("selected_stickers", group_syn["stickers"])
            for emo in emotions:
                if emo in team: continue
                candidates = [s for s in source_stickers if s.emotion == emo]
                if candidates:
                    best = max(candidates, key=lambda s: (sticker_synergy_count[s.address]["count"], s.total_value))
                    team[emo] = best
                    group_added.add(emo)
            if self.count_team_attr(team.values(), group, group_syn.get("attr_value")) < 4:
                for emo in group_added:
                    if emo in team:
                        del team[emo]
        return team


    def build_tribe_teams_v2(self, stickers: List[Sticker], team_size: int = 7) -> Dict:
        """
        Новый алгоритм формирования команд по ТЗ (2026-04-09):
        1. Копируем список стикеров в отдельный список
        2. Внешний бесконечный цикл
        3. Определить какие синергии можно собрать из текущих стикеров
        4. Если синергий из 4 и более элементов нет, то выходим из цикла
        5. Формируем combo_results, аналогично текущему алгоритму
        6. Выбираем combo_result, который дает больший бонус синергий, если таких несколько, то выбираем тот, у которых суммарный бонус стикеров больше
        7. Добавляем combo_result в команды и исключаем стикеры, которые попали в combo_result из списка пункта 1.
        8. Возвращаемся к пункту 3
        9. Сортируем команды по суммарному павер (с бонусами за синергию)
        10. Дополняем команды до полных (недостающими эмоциями, если это возможно по максимальному паверу) стикерами, которые остались в списке из пункта 1. Пересчитываем статистику команд и добавляем их в результирующий список
        11. Если после прохода всех команд остались стикеры, то формируем команды из них (выбираем на каждую эмоцию по макс паверу), считаем статистику и добавляем команды в результирующий список.
        """
        from copy import deepcopy
        from itertools import product
        decision_log = []
        available_stickers = list(stickers)  # 1. Копируем список стикеров
        teams = []  # Список команд (каждая команда - dict с team, synergy_map, total_bonus и т.д.)

        while True:  # 2. Внешний бесконечный цикл
            # 3. Определить синергии из текущих available_stickers
            group_synergies = {g: [None] for g in ATTRIBUTE_GROUPS}
            for group in ATTRIBUTE_GROUPS:
                threshold = self.synergy_thresholds.get(group, 4)
                value_map = self._group_by_attribute_value(available_stickers, group)
                for attr_value, st_list in value_map.items():
                    sy_data = _calculate_synergy_for_value(attr_value, st_list, group)
                    for row in sy_data.get('rows', []):
                        attr_count = row['row_attr_count']
                        if attr_count >= threshold:
                            selected_stickers = list(list(item.get('wallets').values())[0] for item in list(row['emotions'].values()))
                            selected_stickers.sort(key=lambda x: EMOTION_ORDER.index(x.emotion) if x.emotion in EMOTION_ORDER else len(EMOTION_ORDER))
                            synergy = {
                                "group": group,
                                "attr_value": attr_value,
                                "stickers": st_list,
                                "selected_stickers": selected_stickers,
                                "bonus": self.synergy_bonus_table.get(attr_count, 0),
                                "count": attr_count
                            }
                            group_synergies[group].append(synergy)

            # 4. Если нет синергий >=4 элементов, выходим
            has_large_synergy = any(len(syn_list) > 0 for syn_list in group_synergies.values())
            if not has_large_synergy:
                break

            # 5. Формируем combo_results
            all_combos = list(product(*[group_synergies[g] for g in ATTRIBUTE_GROUPS]))
            combo_results = []
            for combo in all_combos:
                used_stickers = []
                synergy_map = {}
                for s in combo:
                    if s:
                        synergy_map[s["group"]] = s
                        used_stickers.extend(s.get("selected_stickers", s["stickers"]))
                if not synergy_map:
                    continue

                sticker_synergy_count = {}
                for group, syn in synergy_map.items():
                    for st in syn.get("selected_stickers", syn["stickers"]):
                        sticker_synergy_count.setdefault(st.address, {"count": 0, "obj": st})
                        sticker_synergy_count[st.address]["count"] += 1
                sticker_objs = [v["obj"] for v in sticker_synergy_count.values()]
                sticker_objs.sort(
                    key=lambda s: (
                        sticker_synergy_count[s.address]["count"],
                        s.total_value,
                        -EMOTION_ORDER.index(s.emotion) if s.emotion in EMOTION_ORDER else -len(EMOTION_ORDER)
                    ),
                    reverse=True
                )

                team = {}
                groups = (
                ("Bracelet", set(BRACELET_EMOTIONS)),
                ("Logos", set(LOGO_EMOTIONS)),
                ("Earrings", EMOTION_ORDER)
                )

                for group, emotions in groups:
                    team = self.add_group_synergy(team, group, synergy_map, emotions, sticker_synergy_count)

                if not team:
                    continue

                real_bonus = self._count_synergy_bonus(team, synergy_map)
                stickers_power = sum(s.total_value for s in team.values())
                team_bonus = 350 if len(team.values()) == team_size else 0
                combo_results.append({
                    "combo": combo,
                    "team": team,
                    "synergy_bonus": real_bonus,
                    "stickers_power": stickers_power,
                    "team_bonus": team_bonus,
                    "total_power": sum((real_bonus, stickers_power, team_bonus))
                })

            if not combo_results:
                break

            # 6. Выбираем лучший combo_result
            combo_results.sort(key=lambda x: (x["synergy_bonus"], x["stickers_power"]), reverse=True)
            best_combo = combo_results[0]

            # 7. Добавляем в команды и исключаем стикеры
            best_combo["synergy_map"] = {s["group"]: s for s in best_combo["combo"] if s}
            teams.append(best_combo)
            used_ids = set(s.address for s in best_combo["team"].values())
            available_stickers = [s for s in available_stickers if s.address not in used_ids]

        # 9. Сортируем команды по суммарному павер (с бонусами)
        teams.sort(key=lambda t: t["total_power"], reverse=True)

        # 10. Дополняем команды до полных
        for t in teams:
            present_emotions = set(s.emotion for s in t["team"].values())
            for emo in EMOTION_ORDER:
                if len(t["team"]) >= team_size:
                    break
                if emo not in present_emotions:
                    candidates = [s for s in available_stickers if s.emotion == emo]
                    if candidates:
                        best = max(candidates, key=lambda s: s.total_value)
                        t["team"][emo] = best
                        available_stickers.remove(best)
                        present_emotions.add(emo)
            # Пересчитываем бонус после дополнения
            t["synergy_bonus"] = self._count_synergy_bonus(t["team"], t["synergy_map"])
            t["stickers_power"] = sum(s.total_value for s in t["team"].values())
            t["team_bonus"] = 350 if len(t["team"].values()) == team_size else 0
            t["total_power"] = sum((t["synergy_bonus"], t["stickers_power"], t["team_bonus"]))

        # 11. Если остались стикеры, формируем команды из них
        extra_teams = []
        while available_stickers:
            team = {}
            used_emotions = set()
            for emo in EMOTION_ORDER:
                if emo in used_emotions:
                    continue
                candidates = [s for s in available_stickers if s.emotion == emo]
                if candidates:
                    best = max(candidates, key=lambda s: s.total_value)
                    team[emo] = best
                    available_stickers.remove(best)
                    used_emotions.add(emo)
                if len(team) >= team_size:
                    break
            if team:
                stickers_power = sum(s.total_value for s in team.values())
                team_bonus = 350 if len(team.values()) == team_size else 0
                extra_teams.append({
                    "team": team,
                    "synergy_bonus": 0,
                    "stickers_power": stickers_power,
                    "team_bonus": team_bonus,
                    "total_power": sum((stickers_power, team_bonus))
                })
            else:
                break
        teams.extend(extra_teams)
        teams.sort(key=lambda t: t["total_power"], reverse=True)
        # Собираем результат
        result_teams = [t["team"] for t in teams]
        team_powers = [t["total_power"] for t in teams]
        result = {
            "teams": result_teams,
            "team_powers": team_powers,
            "total_power": sum(team_powers),
            "decision_log": "\n".join(decision_log),
        }
        return result
    """Build optimal teams maximizing total tribe power, not individual team power."""
    
    def __init__(self, sticker_repo: StickerRepository):
        self.repo = sticker_repo
        self.attribute_groups = ATTRIBUTE_GROUPS
        self.synergy_thresholds = SYNERGY_THRESHOLDS
        self.synergy_bonus_table = {1: 0, 2: 0, 3: 0, 4: 400, 5: 500, 6: 700, 7: 1000}
    
    # ==================== PHASE I: DATA COLLECTION ====================
    
    def build_optimal_tribe_teams(self, stickers: List[Sticker], team_size: int = 7) -> Dict:
        """
        Основной entry point для фронта: использует build_tribe_teams_v2 (старый API).
        Для отладки нового алгоритма используйте debug_build_tribe_teams_v2.py
        """
        return self.build_tribe_teams_v2(stickers, team_size)
        
        # Phase II: Identify and resolve conflicts
        decision_log.append(f"\n[PHASE II] Resolving conflicts")
        conflicts = self._find_conflicts(stickers, all_synergies)
        decision_log.append(f"  Found {len(conflicts)} stickers with conflicts")
        
        selected_synergies = self._resolve_conflicts(all_synergies, conflicts, decision_log)
        decision_log.append(f"  Selected {len(selected_synergies)} synergies for teams")
        
        # Phase III: Build teams
        decision_log.append(f"\n[PHASE III] Building teams from selected synergies")
        teams = self._build_teams_from_synergies(selected_synergies, stickers, team_size, decision_log)
        
        # Phase IV: Calculate metrics
        decision_log.append(f"\n[PHASE IV] Final results")
        total_power = sum(self._calculate_team_power(t, team_size) for t in teams)
        decision_log.append(f"  Total tribe power: {total_power}")
        decision_log.append(f"  Teams formed: {len(teams)}")
        
        failed_synergies = [s for s in all_synergies if s not in selected_synergies]
        
        return {
            "teams": teams,
            "total_power": total_power,
            "synergy_summary": {
                "activated": selected_synergies,
                "failed": failed_synergies,
                "conflicts_resolved": conflicts
            },
            "decision_log": "\n".join(decision_log)
        }
    
    def _gather_all_synergies(self, stickers: List[Sticker]) -> List[Dict]:
        """
        Step 2: Find all possible synergies.
        
        Returns list of synergies with structure:
        {
            "id": "earring_gold_4",
            "group": "Earrings",
            "value": "Gold Ring",
            "attr_count": 4,
            "bonus": 400,
            "stickers": [Sticker, ...],
            "emotions_present": {"Happy": Sticker, "Sad": Sticker, ...}
        }
        """
        synergies = []
        
        for group_name, traits in self.attribute_groups.items():
            # Group stickers by attribute values in this group
            value_map = self._group_by_attribute_value(stickers, group_name)
            
            for attr_value, stickers_with_value in value_map.items():
                # Count unique emotions
                emotions_dict = {}
                for sticker in stickers_with_value:
                    if sticker.emotion not in emotions_dict:
                        emotions_dict[sticker.emotion] = sticker
                
                attr_count = len(emotions_dict)
                threshold = self.synergy_thresholds.get(group_name, 4)
                
                if attr_count >= threshold:
                    synergy_id = f"{group_name.lower()}_{attr_value.lower()}_{attr_count}"
                    bonus = self.synergy_bonus_table.get(attr_count, 0)
                    
                    synergies.append({
                        "id": synergy_id,
                        "group": group_name,
                        "value": attr_value,
                        "attr_count": attr_count,
                        "bonus": bonus,
                        "stickers": stickers_with_value,
                        "emotions_present": emotions_dict
                    })
        
        return synergies
    
    def _group_by_attribute_value(self, stickers: List[Sticker], group_name: str) -> Dict[str, List[Sticker]]:
        """Group stickers by attribute values for a specific attribute group."""
        result = defaultdict(list)
        
        for sticker in stickers:
            values = sticker.get_attribute_values_for_group(group_name)
            for value in values:
                result[value].append(sticker)
        
        return dict(result)
    
    # ==================== PHASE II: CONFLICT RESOLUTION ====================
    
    def _find_conflicts(self, stickers: List[Sticker], synergies: List[Dict]) -> List[Dict]:
        """
        Step 3: Identify stickers participating in multiple synergies (conflicts).
        
        Returns list of conflicts:
        {
            "sticker_address": "addr",
            "sticker_power": 100,
            "involved_in_synergies": [synergy_id1, synergy_id2, ...],
            "type": "binary_conflict" | "ternary_conflict" | "higher_conflict"
        }
        """
        sticker_to_synergies = defaultdict(list)
        
        for synergy in synergies:
            for sticker in synergy["stickers"]:
                sticker_to_synergies[sticker.address].append(synergy["id"])
        
        conflicts = []
        for sticker_addr, synergy_ids in sticker_to_synergies.items():
            if len(synergy_ids) > 1:
                sticker = next(s for s in stickers if s.address == sticker_addr)
                conflict_type = "binary_conflict" if len(synergy_ids) == 2 else "ternary_conflict" if len(synergy_ids) == 3 else "higher_conflict"
                
                conflicts.append({
                    "sticker_address": sticker_addr,
                    "sticker_power": sticker.total_value,
                    "involved_in_synergies": synergy_ids,
                    "type": conflict_type
                })
        
        return conflicts
    
    def _resolve_conflicts(self, synergies: List[Dict], conflicts: List[Dict], decision_log: List[str]) -> List[Dict]:
        """
        Step 4-5: Build conflict graph and resolve using improved partial overlap logic.
        Теперь синергия может быть включена, если хотя бы часть её стикеров свободна (например, >= 50%).
        """
        if not conflicts:
            decision_log.append("  No conflicts, all synergies selected")
            return synergies

        # Build conflict graph: synergy_id -> set of conflicting synergy_ids
        conflict_graph = defaultdict(set)
        synergy_by_id = {s["id"]: s for s in synergies}

        sticker_to_synergies = defaultdict(set)
        for synergy in synergies:
            for sticker in synergy["stickers"]:
                sticker_to_synergies[sticker.address].add(synergy["id"])

        for sticker_addr, synergy_ids in sticker_to_synergies.items():
            synergy_list = list(synergy_ids)
            for i, s1 in enumerate(synergy_list):
                for s2 in synergy_list[i+1:]:
                    conflict_graph[s1].add(s2)
                    conflict_graph[s2].add(s1)

        # Greedy selection: sort by conflict count (ascending), then by bonus (descending)
        synergy_scores = []
        for s in synergies:
            conflict_count = len(conflict_graph[s["id"]])
            score = (conflict_count, -s["bonus"])  # Sort by conflict count first, then by bonus descending
            synergy_scores.append((score, s))

        synergy_scores.sort(key=lambda x: x[0])

        selected = set()
        selected_synergies = []
        blocked_stickers = set()

        for score, synergy in synergy_scores:
            synergy_stickers = {s.address for s in synergy["stickers"]}
            free_stickers = synergy_stickers - blocked_stickers
            free_ratio = len(free_stickers) / max(1, len(synergy_stickers))

            if free_ratio >= 0.5:
                # Добавляем синергию, используя только свободные стикеры
                selected.add(synergy["id"])
                # Копируем синергию, оставляя только свободные стикеры
                partial_synergy = dict(synergy)
                partial_synergy["stickers"] = [s for s in synergy["stickers"] if s.address in free_stickers]
                partial_synergy["attr_count"] = len(partial_synergy["stickers"])
                selected_synergies.append(partial_synergy)
                blocked_stickers.update(free_stickers)
                decision_log.append(f"    ✓ Partially selected {synergy['id']} ({len(free_stickers)}/{len(synergy_stickers)} stickers, +{synergy['bonus']} PWR)")
            else:
                decision_log.append(f"    ✗ Skipped {synergy['id']} (not enough free stickers: {len(free_stickers)}/{len(synergy_stickers)})")

        return selected_synergies
    
    # ==================== PHASE III: TEAM FORMATION ====================
    
    def _build_teams_from_synergies(self, selected_synergies: List[Dict], 
                                   all_stickers: List[Sticker], 
                                   team_size: int,
                                   decision_log: List[str]) -> List[List[Sticker]]:
        """
        Step 6-8: Form teams from selected synergies.
        
        Algorithm:
        1. Mark synergy stickers as "reserved"
        2. Loop: pick a synergy core, fill missing emotions, pad to team_size
        3. Handle remainders
        """
        teams = []
        
        # Separate stickers
        synergy_stickers_by_emotion = defaultdict(list)  # Group synergy stickers by emotion
        reserved_stickers = set()
        
        for synergy in selected_synergies:
            for sticker in synergy["stickers"]:
                reserved_stickers.add(sticker.address)
                synergy_stickers_by_emotion[sticker.emotion].append(sticker)
        
        free_stickers = [s for s in all_stickers if s.address not in reserved_stickers]
        
        decision_log.append(f"  Reserved stickers: {len(reserved_stickers)}")
        decision_log.append(f"  Free stickers: {len(free_stickers)}")
        
        # Build teams
        used_synergy_cores = set()
        
        while reserved_stickers:
            team = []
            synergy_used = None
            
            # Try to pick an unused synergy as core
            for synergy in selected_synergies:
                synergy_id = synergy["id"]
                if synergy_id not in used_synergy_cores:
                    # Check if synergy stickers are still available
                    synergy_stickers_available = [s for s in synergy["stickers"] if s.address in reserved_stickers]
                    
                    if len(synergy_stickers_available) >= synergy["attr_count"] * 0.5:  # At least half available
                        # Use this synergy as core
                        for emotion, sticker in synergy["emotions_present"].items():
                            if sticker.address in reserved_stickers:
                                team.append(sticker)
                                reserved_stickers.discard(sticker.address)
                        synergy_used = synergy_id
                        used_synergy_cores.add(synergy_id)
                        break
            
            # If no suitable synergy, use strongest reserved stickers
            # if not team and reserved_stickers:
            #     # Pick strongest available
            #     reserved_list = [s for s in all_stickers if s.address in reserved_stickers]
            #     reserved_list.sort(key=lambda s: s.total_value, reverse=True)
            #
            #     team = reserved_list[:min(team_size, len(reserved_list))]
            #     for s in team:
            #         reserved_stickers.discard(s.address)
            
            # Fill missing emotions from free stickers
            present_emotions = {s.emotion for s in team}
            for emotion in EMOTION_ORDER:
                if emotion not in present_emotions and team:
                    candidates = [s for s in free_stickers if s.emotion == emotion and s not in team]
                    if candidates:
                        best = max(candidates, key=lambda s: s.total_value)
                        team.append(best)
                        free_stickers.remove(best)
                        present_emotions.add(emotion)
            
            # Pad to team_size from free stickers
            if len(team) < team_size:
                for s in free_stickers:
                    if len(team) >= team_size:
                        break
                    if s not in team:
                        team.append(s)
            
            if team:
                teams.append(team)
                decision_log.append(f"  Team {len(teams)}: {len(team)} stickers, synergy={synergy_used or 'none'}")
        
        # Handle free stickers (remainders)
        if free_stickers:
            free_stickers.sort(key=lambda s: s.total_value, reverse=True)
            
            while free_stickers:
                team = free_stickers[:team_size]
                teams.append(team)
                free_stickers = free_stickers[team_size:]
                decision_log.append(f"  Team {len(teams)}: {len(team)} stickers (remainder)")
        
        return teams
    
    # ==================== PHASE IV: METRICS & POWER CALCULATION ====================
    
    def _calculate_team_power(self, team: List[Sticker], team_size: int) -> float:
        """Calculate total power of a team including bonuses."""
        base_power = sum(s.total_value for s in team)
        
        # Full team bonus
        full_team_bonus = 350 if len(team) >= team_size else 0
        
        # Synergy bonuses (would need to pass synergy info, for now just base + full)
        # In full implementation, track which synergies are in this team
        
        return base_power + full_team_bonus
    
    def _build_strong_teams(self, stickers: List[Sticker], team_size: int) -> List[List[Sticker]]:
        """Fallback: build teams by strongest emotion."""
        remaining = list(stickers)
        teams = []
        
        while remaining:
            team = []
            for emotion in EMOTION_ORDER:
                candidates = [s for s in remaining if s.emotion == emotion]
                if candidates:
                    best = max(candidates, key=lambda s: s.total_value)
                    team.append(best)
                    remaining.remove(best)
                
                if len(team) >= team_size:
                    break
            
            if team:
                teams.append(team)
            else:
                break
        
        if remaining:
            # Handle remainders
            remaining.sort(key=lambda s: s.total_value, reverse=True)
            while remaining:
                team = remaining[:team_size]
                teams.append(team)
                remaining = remaining[team_size:]
        
        return teams
    
    def _sticker_power(self, s: Sticker) -> float:
        """Get raw power of a sticker."""
        return getattr(s, "total_value", 0) or 0
