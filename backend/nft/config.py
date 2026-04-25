
NFT_VALUES = {
    "ZarGates GiftBox": 10,
    "Common StickerBox": 10,
    "Epic StickerBox": 20,
    "Legendary StickerBox": 30,
}

anagram = {
    "Fake Gold": "Fake",
    "Golden": "Gold",
    "Wallpaper": "Paper",
    "Mechanic’s": "Mechanic",
    "Mechanical": "Mechanic",
    "Magical": "Magic",
    "Bones": "Bone",
    "Mushrooms": "Mushroom",
}

EMOTIONS = {
    "In Love": ["Skin Tone", "Earrings", "Heart", "Armor"],
    "Greeting": ["Skin Tone", "Earrings", "Cup", "Glasses"],
    "Capped": ["Skin Tone", "Earrings", "Cap", "Ring"],
    "Shoked": ["Skin Tone", "Earrings", "Pendant Chain", "Bracelet"],
    "Do Something": ["Skin Tone", "Earrings", "Stick", "Bracelet"],
    "To The Moon": ["Skin Tone", "Earrings", "Hamster", "Bracelet"],
    "Wen TGE": ["Skin Tone", "Earrings", "Sign", "Bracelet"]
}


COLLECTIONS = {
    "Unstoppable Tribe from ZarGates": {
        "address": "EQBGNoXXfQR07HdDhtkmIu1ojTTwcjB0EhHYOMSH3P7sZGJR",
        "box_collection": "ZarGates StickerBoxes"
    },
    "ZarGates StickerBoxes": {
        "address": "EQBzPVuHoSR_QlBFtyJiyDfJdKy-dp2sOBbY0s0BBSzaMps7",
        "box_collection": "ZarGates GiftBoxes"
    },
    "ZarGates GiftBoxes": {
        "address": "EQD1YVbwG5dNV9lZgz18F4cjBm5iqYXyeUqdGe21JXjsLCIo",
    }
}

# For reverse lookup
COLLECTIONS_BY_ADDRESS = {info["address"]: name for name, info in COLLECTIONS.items()}

LOGO_EQUIV = {
    "Professor TON": "TON",
    "Zargates Business": "Zargates"
}

ATTRIBUTE_GROUPS = {
    "Earrings": {"Earrings", "Earring"},
    "Bracelet": {"Bracelet"},
    "Logos": {"Heart", "Cup", "Cap", "Pendant Chain", "Hamster", "Armor", "Glasses", "Ring"},
    "Tribe": {"Skin Tone"},
}


ICONS = {
  "Skin Tone": "👨‍👨‍👦‍👦",
  "Earrings": "✨",
  "Heart": "❤️",
  "Cup": "🥤",
  "Cap": "🧢",
  "Pendant Chain": "📿",
  "Stick": "🏒",
  "Hamster": "🐹",
  "Sign": "📜",
  "Armor": "🛡️",
  "Glasses": "👓",
  "Ring": "💍",
  "Bracelet": "⌚️",
  'Logos': '👑',
  'attribute': '️⚔️',
  'synergy': '🔗',
  'name': '⭐',
}