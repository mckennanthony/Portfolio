# clothing_item.py

class ClothingItem:
    """Represents one item in the closet."""

    def __init__(
        self,
        name: str,
        category: str,
        color: str = "",
        vibe: str = "Any",
        image_path: str = ""
    ):
        self.name = name.strip()
        # Category can be: "Top", "Bottom", "Shoes", "Accessory", "Dress"
        self.category = category.strip()
        self.color = color.strip()
        self.vibe = vibe.strip() or "Any"
        self.image_path = image_path.strip()

    def __str__(self):
        parts = [self.name]
        if self.color:
            parts.append(f"({self.color})")
        if self.vibe and self.vibe != "Any":
            parts.append(f"[{self.vibe}]")
        return " ".join(parts)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "color": self.color,
            "vibe": self.vibe,
            "image_path": self.image_path,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data.get("name", "Unnamed"),
            category=data.get("category", "Unknown"),
            color=data.get("color", ""),
            vibe=data.get("vibe", "Any"),
            image_path=data.get("image_path", ""),
        )
