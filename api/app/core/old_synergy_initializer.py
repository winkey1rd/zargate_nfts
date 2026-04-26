"""
Synergy Initializer - Pre-processes all synergies and caches them in stickers.

This module uses SynergyEngine to compute synergies correctly, then caches results 
in each sticker's synergies_json field for fast access during card display.
"""

from typing import Dict, List, Set
from collections import defaultdict
import logging

from transfer_app.db.models import Sticker
from transfer_app.db.repositories import StickerRepository
from transfer_app.config.config import ATTRIBUTE_GROUPS, SYNERGY_THRESHOLDS
from transfer_app.core.synergy_engine import SynergyEngine

logger = logging.getLogger(__name__)


class SynergyInitializer:
    """Initialize and cache synergies using SynergyEngine."""
    
    def __init__(self, sticker_repo: StickerRepository):
        self.repo = sticker_repo
        self.synergy_engine = SynergyEngine(sticker_repo)
        self.attribute_groups = ATTRIBUTE_GROUPS
        self.synergy_thresholds = SYNERGY_THRESHOLDS
    
    def initialize_all_synergies(self) -> Dict[str, int]:
        """
        Cache all synergies computed by SynergyEngine.
        
        Process:
        1. Group stickers by skin_tone
        2. For each skin_tone, use SynergyEngine to compute synergies
        3. Filter synergies by threshold and assign to participating stickers
        4. Store in database for fast access
        
        Returns:
            {
                "total_synergies_found": int,
                "total_stickers_with_synergies": int,
                "by_skin_tone": {skin_tone: count, ...}
            }
        """
        session = self.repo.session
        all_stickers = session.query(Sticker).all()
        
        logger.info(f"Initializing synergies for {len(all_stickers)} stickers (using SynergyEngine)")
        
        # Group stickers by skin tone
        by_skin_tone = defaultdict(list)
        for sticker in all_stickers:
            by_skin_tone[sticker.skin_tone].append(sticker)
        
        total_synergies_found = 0
        total_with_synergies = set()
        by_skin_tone_stats = {}
        
        # Process each skin tone
        for skin_tone, stickers_in_tribe in by_skin_tone.items():
            logger.info(f"  Processing {skin_tone} ({len(stickers_in_tribe)} stickers)")
            
            synergies_to_cache = self._compute_and_filter_synergies(skin_tone)
            
            # Assign synergies to stickers
            stickers_assigned = set()
            for synergy_entry in synergies_to_cache:
                for sticker in synergy_entry["stickers"]:
                    # Add this synergy to sticker's cache
                    existing_synergies = sticker.get_synergies()
                    
                    cached_entry = {
                        "group_name": synergy_entry["group"],
                        "attr_value": synergy_entry["value"],
                        "max_row_count": synergy_entry["max_row_count"]
                    }
                    
                    # Avoid duplicates
                    if cached_entry not in existing_synergies:
                        existing_synergies.append(cached_entry)
                        sticker.set_synergies(existing_synergies)
                    
                    stickers_assigned.add(sticker.id)
                    total_with_synergies.add(sticker.id)
            
            total_synergies_found += len(synergies_to_cache)
            by_skin_tone_stats[skin_tone] = {
                "synergies": len(synergies_to_cache),
                "stickers_assigned": len(stickers_assigned)
            }
            
            logger.info(f"    Cached {len(synergies_to_cache)} synergies for {len(stickers_assigned)} stickers")
        
        # Commit changes
        try:
            session.commit()
            logger.info(f"✓ Successfully cached all synergies")
        except Exception as e:
            session.rollback()
            logger.error(f"✗ Error caching synergies: {e}")
            raise
        
        return {
            "total_synergies_found": total_synergies_found,
            "total_stickers_with_synergies": len(total_with_synergies),
            "by_skin_tone": by_skin_tone_stats
        }
    
    def _compute_and_filter_synergies(self, skin_tone: str) -> List[Dict]:
        """
        Use SynergyEngine to compute synergies with correct attribute counts.
        Filter by threshold and collect all stickers participating.
        
        Returns list of synergies ready to cache:
        {
            "group": "Earrings",
            "value": "Gold Ring",
            "max_row_count": 5,  <- quantity of ATTRIBUTES (from SynergyEngine)
            "stickers": [Sticker, Sticker, ...]
        }
        """
        synergies_to_cache = []
        
        # Get all stickers for this skin tone
        session = self.repo.session
        tribe_stickers = session.query(Sticker).filter(Sticker.skin_tone == skin_tone).all()
        
        if not tribe_stickers:
            return []
        
        # Use SynergyEngine to compute synergies for each group
        for group_name in self.attribute_groups.keys():
            # Build synergies using engine (engine correctly counts attributes)
            synergy_results = self.synergy_engine.build_synergies(group_name, skin_tone)
            
            # Process results
            threshold = self.synergy_thresholds.get(group_name, 4)
            
            for attr_value, synergy_data in synergy_results.items():
                rows = synergy_data.get('rows', [])
                
                if not rows:
                    continue
                
                # Collect all stickers from ALL rows of this synergy
                all_stickers_in_synergy = set()
                for row in rows:
                    for emotion_info in row.get('emotions', {}).values():
                        for sticker in emotion_info.get('wallets', {}).values():
                            if isinstance(sticker, Sticker):
                                all_stickers_in_synergy.add(sticker)
                
                # Get max_row_count from SynergyEngine (quantity of attributes)
                max_row_count = synergy_data.get('max_row_count', 0)
                
                # Only cache if attribute count meets threshold
                if max_row_count >= threshold:
                    synergies_to_cache.append({
                        "group": group_name,
                        "value": attr_value,
                        "max_row_count": max_row_count,  # <- CORRECT: from SynergyEngine
                        "stickers": list(all_stickers_in_synergy)
                    })
        
        return synergies_to_cache
    
    def clear_all_synergies(self) -> int:
        """Clear all synergy assignments from stickers."""
        session = self.repo.session
        all_stickers = session.query(Sticker).all()
        
        count = 0
        for sticker in all_stickers:
            if sticker.get_synergies():
                sticker.set_synergies([])
                count += 1
        
        try:
            session.commit()
            logger.info(f"✓ Cleared synergies from {count} stickers")
        except Exception as e:
            session.rollback()
            logger.error(f"✗ Error clearing synergies: {e}")
            raise
        
        return count
