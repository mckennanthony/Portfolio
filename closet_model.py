# closet_model.py
import random
from clothing_item import ClothingItem

# Now includes Dress
CATEGORIES = ["Top", "Bottom", "Shoes", "Accessory", "Dress"]

VIBES = [
    "Any",
    "Casual",
    "Comfy",
    "Dressy",
    "Sporty",
    "Going Out",
    "Game Day",
]


class Closet:
    """Holds all clothing items and handles outfit generation."""

    def __init__(self):
        self.items = []      # list of ClothingItem
        self.favorites = []  # list of dicts

    def add_item(self, item: ClothingItem):
        self.items.append(item)

    def get_items_by_category_and_vibe(self, category: str, vibe: str | None):
        """Return all items for a category filtered by vibe."""
        if vibe is None or vibe == "Any":
            return [item for item in self.items if item.category == category]

        return [
            item for item in self.items
            if item.category == category and (item.vibe == vibe or item.vibe == "Any")
        ]

    def random_outfit(self, vibe: str | None = None, include_accessory: bool = True):
        """
        Build a random outfit.

        Keys in the outfit dict:
        - "Top", "Bottom", "Dress", "Shoes", "Accessory"

        If a Dress is chosen, Top and Bottom will be None.
        """
        outfit = {
            "Top": None,
            "Bottom": None,
            "Dress": None,
            "Shoes": None,
            "Accessory": None,
        }

        shoes = self.get_items_by_category_and_vibe("Shoes", vibe)
        outfit["Shoes"] = random.choice(shoes) if shoes else None

        if include_accessory:
            acc = self.get_items_by_category_and_vibe("Accessory", vibe)
            outfit["Accessory"] = random.choice(acc) if acc else None

        dresses = self.get_items_by_category_and_vibe("Dress", vibe)
        tops = self.get_items_by_category_and_vibe("Top", vibe)
        bottoms = self.get_items_by_category_and_vibe("Bottom", vibe)

        use_dress = False
        if dresses and (not tops or not bottoms):
            use_dress = True
        elif dresses and tops and bottoms:
            use_dress = random.choice([True, False])

        if use_dress:
            outfit["Dress"] = random.choice(dresses)
        else:
            outfit["Top"] = random.choice(tops) if tops else None
            outfit["Bottom"] = random.choice(bottoms) if bottoms else None

        return outfit

    def add_favorite(self, outfit: dict, name: str = ""):
        fav = {
            "label": name or "Favorite outfit",
            "outfit": {
                cat: item.to_dict() if item else None
                for cat, item in outfit.items()
            }
        }
        self.favorites.append(fav)

    def to_dict(self) -> dict:
        return {
            "items": [item.to_dict() for item in self.items],
            "favorites": self.favorites,
        }

    @classmethod
    def from_dict(cls, data: dict):
        closet = cls()
        for item_data in data.get("items", []):
            closet.add_item(ClothingItem.from_dict(item_data))
        closet.favorites = data.get("favorites", [])
        return closet
