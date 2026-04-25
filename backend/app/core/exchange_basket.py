"""
Exchange basket functionality for managing stickers across multiple wallets.
"""
from collections import defaultdict
from typing import Dict, List, Set
from dataclasses import dataclass, field


@dataclass
class BasketSection:
    """Represents a wallet's section in the exchange basket."""
    wallet_address: str
    stickers: List = field(default_factory=list)

    def add_sticker(self, sticker):
        """Add sticker to basket section."""
        self.stickers.append(sticker)

    def remove_sticker(self, sticker_address: str):
        """Remove sticker from basket section."""
        self.stickers = [s for s in self.stickers if s.address != sticker_address]

    def get_orc_count(self) -> int:
        """Get total number of orcs (stickers) in section."""
        return len(self.stickers)

    def get_total_points(self) -> float:
        """Get total value/points in section."""
        return sum(s.total_value for s in self.stickers)

    def get_synergies_count(self) -> Dict[str, int]:
        """
        Get count of synergies stickers participate in.
        Returns dict mapping synergy to count of stickers with that synergy.
        """
        synergies = defaultdict(int)
        for sticker in self.stickers:
            # Count based on sticker attributes
            for attr, value in sticker.attributes.items():
                synergy_key = f"{attr}:{value}"
                synergies[synergy_key] += 1
        return synergies

    def get_average_value(self) -> float:
        """Get average value per sticker in section."""
        if not self.stickers:
            return 0
        return self.get_total_points() / self.get_orc_count()


class ExchangeBasket:
    """Main exchange basket managing multiple wallet sections."""

    def __init__(self):
        self.sections: Dict[str, BasketSection] = {}
        self.sticker_addresses: Set[str] = set()  # Track all stickers in basket

    def create_section(self, wallet_address: str):
        """Create a new basket section for a wallet."""
        if wallet_address not in self.sections:
            self.sections[wallet_address] = BasketSection(wallet_address)

    def add_sticker(self, wallet_address: str, sticker):
        """Add sticker to a wallet's section."""
        if wallet_address not in self.sections:
            self.create_section(wallet_address)

        if sticker.address not in self.sticker_addresses:
            self.sections[wallet_address].add_sticker(sticker)
            self.sticker_addresses.add(sticker.address)
            return True
        return False  # Sticker already in basket

    def remove_sticker(self, wallet_address: str, sticker_address: str):
        """Remove sticker from a wallet's section."""
        if wallet_address in self.sections:
            self.sections[wallet_address].remove_sticker(sticker_address)
            self.sticker_addresses.discard(sticker_address)

    def get_section_stats(self, wallet_address: str) -> Dict:
        """Get statistics for a specific wallet's section."""
        if wallet_address not in self.sections:
            return {}

        section = self.sections[wallet_address]
        synergies = section.get_synergies_count()

        return {
            'wallet': wallet_address,
            'orc_count': section.get_orc_count(),
            'total_points': section.get_total_points(),
            'average_value': section.get_average_value(),
            'synergies_count': len(synergies),
            'synergy_details': synergies
        }

    def get_all_stats(self) -> Dict:
        """Get statistics for all sections."""
        all_stats = {}
        for wallet_address in self.sections:
            all_stats[wallet_address] = self.get_section_stats(wallet_address)
        return all_stats

    def get_total_stats(self) -> Dict:
        """Get total statistics across all wallets."""
        total_stickers = sum(len(section.stickers) for section in self.sections.values())
        total_points = sum(section.get_total_points() for section in self.sections.values())
        total_synergies = sum(
            len(section.get_synergies_count())
            for section in self.sections.values()
        )

        return {
            'total_stickers': total_stickers,
            'total_points': total_points,
            'total_synergies': total_synergies,
            'wallets_count': len(self.sections),
            'average_value_per_sticker': total_points / total_stickers if total_stickers > 0 else 0
        }

    def clear(self):
        """Clear all sections from basket."""
        self.sections.clear()
        self.sticker_addresses.clear()

    def get_stickers_for_wallet(self, wallet_address: str) -> List:
        """Get all stickers in a wallet's section."""
        if wallet_address in self.sections:
            return self.sections[wallet_address].stickers
        return []

    def is_sticker_in_basket(self, sticker_address: str) -> bool:
        """Check if sticker is already in basket."""
        return sticker_address in self.sticker_addresses
