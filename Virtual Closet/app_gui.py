# app_gui.py
import os
import tkinter as tk
from tkinter import messagebox, filedialog

from PIL import Image, ImageTk

from clothing_item import ClothingItem
from closet_model import Closet, CATEGORIES, VIBES
from storage import load_closet, save_closet


class SquigglePanel(tk.Frame):
    """Canvas with a zigzag border and an inner Frame for content."""
    def __init__(self, parent, width=360, height=500,
                 bg_main="#FFEAF6", border_color="#E3C8FF", inner_bg="#FFF9FF"):
        super().__init__(parent, bg=bg_main)

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=bg_main,
            highlightthickness=0
        )
        self.canvas.pack()

        margin = 10
        self._draw_border(width, height, margin, border_color)

        self.inner = tk.Frame(self.canvas, bg=inner_bg)
        self.canvas.create_window(
            width // 2,
            height // 2,
            window=self.inner,
            width=width - margin * 2,
            height=height - margin * 2
        )

    def _draw_border(self, w, h, m, color):
        step = 14
        amp = 4

        # Top
        pts = []
        x = m
        d = 1
        while x <= w - m:
            pts.extend([x, m + d * amp])
            x += step
            d *= -1
        self.canvas.create_line(pts, fill=color, width=3)

        # Bottom
        pts = []
        x = m
        d = -1
        while x <= w - m:
            pts.extend([x, h - m + d * amp])
            x += step
            d *= -1
        self.canvas.create_line(pts, fill=color, width=3)

        # Left
        pts = []
        y = m
        d = 1
        while y <= h - m:
            pts.extend([m + d * amp, y])
            y += step
            d *= -1
        self.canvas.create_line(pts, fill=color, width=3)

        # Right
        pts = []
        y = m
        d = -1
        while y <= h - m:
            pts.extend([w - m + d * amp, y])
            y += step
            d *= -1
        self.canvas.create_line(pts, fill=color, width=3)


class OutfitApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Y2K Virtual Closet")

        # Theme
        self.bg_main = "#FFEAF6"
        self.bg_panel = "#FFF9FF"
        self.button_bg = "#FFD6F2"
        self.button_active = "#FFC0E0"
        self.accent = "#C2E7FF"
        self.accent2 = "#E3C8FF"

        self.root.configure(bg=self.bg_main)

        self.closet: Closet = load_closet()
        self.selected_index = None

        # keep image references alive (current outfit)
        self.outfit_images = {
            "TopOrDress": None,
            "Bottom": None,
            "Shoes": None,
            "Accessory": None,
        }
        # favorite preview images
        self.favorite_images = {
            "TopOrDress": None,
            "Bottom": None,
            "Shoes": None,
            "Accessory": None,
        }

        # ----- Header -----
        title = tk.Label(
            root, text="Y2K Virtual Closet",
            font=("Comic Sans MS", 20, "bold"),
            bg=self.bg_main
        )
        title.pack(pady=(10, 0))

        subtitle = tk.Label(
            root,
            text="Pick a vibe and let the closet do the styling ✨",
            font=("Comic Sans MS", 10),
            bg=self.bg_main
        )
        subtitle.pack(pady=(0, 10))

        container = tk.Frame(root, bg=self.bg_main)
        container.pack(padx=10, pady=10, fill="both", expand=True)

        # Left panel: Add to Closet
        left_panel = SquigglePanel(
            container,
            width=560,
            height=880,
            bg_main=self.bg_main,
            border_color=self.accent2,
            inner_bg=self.bg_panel
        )
        left_panel.pack(side="left", padx=8, pady=5)
        self._build_left(left_panel.inner)

        # Middle panel: Today's Outfit
        mid_panel = SquigglePanel(
            container,
            width=560,
            height=880,
            bg_main=self.bg_main,
            border_color=self.accent,
            inner_bg=self.bg_panel
        )
        mid_panel.pack(side="left", padx=8, pady=5)
        self._build_middle(mid_panel.inner)

        # Right panel: Saved Outfits
        fav_panel = SquigglePanel(
            container,
            width=560,
            height=880,
            bg_main=self.bg_main,
            border_color="#FFB3C6",
            inner_bg=self.bg_panel
        )
        fav_panel.pack(side="left", padx=8, pady=5)
        self._build_favorites_panel(fav_panel.inner)

        self._refresh_closet()
        self._refresh_favorites()

        # initial empty previews
        empty_outfit = {
            "Top": None,
            "Bottom": None,
            "Dress": None,
            "Shoes": None,
            "Accessory": None,
        }
        self._update_outfit_images(empty_outfit)
        self._update_favorite_preview(empty_outfit)

    # ---------------- LEFT PANEL (Closet) ----------------
    def _build_left(self, frame: tk.Frame):
        tk.Label(
            frame, text="Add to Closet",
            font=("Comic Sans MS", 13, "bold"),
            bg=self.bg_panel
        ).pack(pady=5)

        # Category
        tk.Label(frame, text="Category:", bg=self.bg_panel).pack(anchor="w")
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        cat_menu = tk.OptionMenu(frame, self.category_var, *CATEGORIES)
        cat_menu.config(bg=self.button_bg, activebackground=self.button_active)
        cat_menu.pack(fill="x", pady=2)

        # Name
        tk.Label(frame, text="Item name:", bg=self.bg_panel).pack(anchor="w")
        self.name_entry = tk.Entry(frame)
        self.name_entry.pack(fill="x", pady=2)

        # Color
        tk.Label(frame, text="Color (optional):", bg=self.bg_panel).pack(anchor="w")
        self.color_entry = tk.Entry(frame)
        self.color_entry.pack(fill="x", pady=2)

        # Vibe
        tk.Label(frame, text="Vibe:", bg=self.bg_panel).pack(anchor="w")
        self.vibe_var = tk.StringVar(value="Any")
        vibe_menu = tk.OptionMenu(frame, self.vibe_var, *VIBES)
        vibe_menu.config(bg=self.button_bg, activebackground=self.button_active)
        vibe_menu.pack(fill="x", pady=2)

        # Image path
        tk.Label(frame, text="Image (PNG path, optional):",
                 bg=self.bg_panel).pack(anchor="w")
        img_row = tk.Frame(frame, bg=self.bg_panel)
        img_row.pack(fill="x", pady=2)
        self.image_entry = tk.Entry(img_row)
        self.image_entry.pack(side="left", fill="x", expand=True)
        tk.Button(
            img_row, text="Browse",
            command=self._browse_image,
            bg=self.button_bg,
            activebackground=self.button_active
        ).pack(side="left", padx=3)

        # Buttons: Add / Update / Delete
        btn_row = tk.Frame(frame, bg=self.bg_panel)
        btn_row.pack(pady=5, fill="x")
        tk.Button(
            btn_row, text="Add",
            command=self._add_item,
            bg=self.button_bg,
            activebackground=self.button_active,
            width=7
        ).pack(side="left", padx=2)
        tk.Button(
            btn_row, text="Update",
            command=self._update_item,
            bg=self.accent2,
            activebackground=self.button_active,
            width=8
        ).pack(side="left", padx=2)
        tk.Button(
            btn_row, text="Delete",
            command=self._delete_item,
            bg="#FFB3C6",
            activebackground=self.button_active,
            width=8
        ).pack(side="left", padx=2)

        # Closet list
        tk.Label(
            frame, text="Closet Items:",
            font=("Comic Sans MS", 11, "bold"),
            bg=self.bg_panel
        ).pack(pady=(8, 2))

        self.closet_listbox = tk.Listbox(frame, height=13, width=45)
        self.closet_listbox.pack(fill="both", expand=True, pady=2)
        self.closet_listbox.bind("<<ListboxSelect>>", self._on_select_item)

        tk.Button(
            frame, text="Save Closet 💾",
            command=self._save_closet,
            bg=self.button_bg,
            activebackground=self.button_active
        ).pack(pady=5)

    def _browse_image(self):
        path = filedialog.askopenfilename(
            title="Choose PNG image",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if path:
            self.image_entry.delete(0, tk.END)
            self.image_entry.insert(0, path)

    # ---------------- MIDDLE PANEL (Today's Outfit) ----------------
    def _build_middle(self, frame: tk.Frame):
        tk.Label(
            frame, text="Today's Outfit",
            font=("Comic Sans MS", 13, "bold"),
            bg=self.bg_panel
        ).pack(pady=5)

        # Today's vibe
        vibe_row = tk.Frame(frame, bg=self.bg_panel)
        vibe_row.pack(pady=5, fill="x")
        tk.Label(vibe_row, text="Today's vibe:", bg=self.bg_panel).pack(side="left")
        self.today_vibe_var = tk.StringVar(value="Any")
        tv_menu = tk.OptionMenu(vibe_row, self.today_vibe_var, *VIBES)
        tv_menu.config(bg=self.button_bg, activebackground=self.button_active)
        tv_menu.pack(side="left", padx=5)

        # Text outfit info
        self.outfit_labels = {}
        for cat in ["Top", "Bottom", "Dress", "Shoes", "Accessory"]:
            row = tk.Frame(frame, bg=self.bg_panel)
            row.pack(anchor="w", pady=1, fill="x")
            tk.Label(row, text=f"{cat}:", width=10, anchor="w",
                     bg=self.bg_panel).pack(side="left")
            lbl = tk.Label(row, text="(none)", anchor="w", bg=self.bg_panel)
            lbl.pack(side="left", fill="x")
            self.outfit_labels[cat] = lbl

        self.include_accessory_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            frame,
            text="Include accessory",
            variable=self.include_accessory_var,
            bg=self.bg_panel
        ).pack(pady=3)

        tk.Button(
            frame, text="Pick My Outfit!",
            command=self._pick_outfit,
            bg=self.accent,
            activebackground=self.button_active
        ).pack(pady=5)

        # Outfit preview (STACKED like paper dolls)
        tk.Label(
            frame, text="Outfit Preview:",
            font=("Comic Sans MS", 11, "bold"),
            bg=self.bg_panel
        ).pack(pady=(6, 2))

        preview = tk.Frame(frame, bg=self.bg_panel)
        preview.pack(pady=2)

        # each canvas: 160x70 so 4 of them fit easily
        self.preview_canvases = {
            "TopOrDress": tk.Canvas(preview, width=200, height=120,
                                    bg="#FFFFFF", highlightthickness=1,
                                    highlightbackground="#000000"),
            "Bottom": tk.Canvas(preview, width=200, height=120,
                                bg="#FFFFFF", highlightthickness=1,
                                highlightbackground="#000000"),
            "Shoes": tk.Canvas(preview, width=200, height=120,
                               bg="#FFFFFF", highlightthickness=1,
                               highlightbackground="#000000"),
            "Accessory": tk.Canvas(preview, width=200, height=120,
                                   bg="#FFFFFF", highlightthickness=1,
                                   highlightbackground="#000000"),
        }

        self.preview_canvases["TopOrDress"].pack(pady=3)
        self.preview_canvases["Bottom"].pack(pady=3)
        self.preview_canvases["Shoes"].pack(pady=3)
        self.preview_canvases["Accessory"].pack(pady=3)

        # Save favorite controls (name + button)
        fav_row = tk.Frame(frame, bg=self.bg_panel)
        fav_row.pack(pady=5, fill="x")
        tk.Label(fav_row, text="Favorite name:", bg=self.bg_panel).pack(side="left")
        self.favorite_name_entry = tk.Entry(fav_row)
        self.favorite_name_entry.pack(side="left", fill="x", expand=True, padx=3)
        tk.Button(
            fav_row, text="Save ⭐",
            command=self._save_favorite,
            bg=self.button_bg,
            activebackground=self.button_active
        ).pack(side="left")

    # ---------------- RIGHT PANEL (Saved Outfits) ----------------
    def _build_favorites_panel(self, frame: tk.Frame):
        tk.Label(
            frame, text="Saved Outfits",
            font=("Comic Sans MS", 13, "bold"),
            bg=self.bg_panel
        ).pack(pady=5)

        # list of saved outfits
        self.favorites_listbox = tk.Listbox(frame, height=7)
        self.favorites_listbox.pack(fill="both", expand=False, pady=(2, 4))
        self.favorites_listbox.bind("<<ListboxSelect>>", self._on_select_favorite)

        # details text
        tk.Label(
            frame, text="Favorite details:",
            font=("Comic Sans MS", 11, "bold"),
            bg=self.bg_panel
        ).pack(pady=(4, 2))

        self.favorite_detail_labels = {}
        for cat in ["Top", "Bottom", "Dress", "Shoes", "Accessory"]:
            row = tk.Frame(frame, bg=self.bg_panel)
            row.pack(anchor="w", pady=1, fill="x")
            tk.Label(row, text=f"{cat}:", width=10, anchor="w",
                     bg=self.bg_panel).pack(side="left")
            lbl = tk.Label(row, text="(none)", anchor="w", bg=self.bg_panel)
            lbl.pack(side="left", fill="x")
            self.favorite_detail_labels[cat] = lbl

        # preview for saved outfit
        tk.Label(
            frame, text="Saved Outfit Preview:",
            font=("Comic Sans MS", 11, "bold"),
            bg=self.bg_panel
        ).pack(pady=(6, 2))

        preview = tk.Frame(frame, bg=self.bg_panel)
        preview.pack(pady=2)

        self.favorite_preview_canvases = {
            "TopOrDress": tk.Canvas(preview, width=200, height=120,
                                    bg="#FFFFFF", highlightthickness=1,
                                    highlightbackground="#000000"),
            "Bottom": tk.Canvas(preview, width=200, height=120,
                                bg="#FFFFFF", highlightthickness=1,
                                highlightbackground="#000000"),
            "Shoes": tk.Canvas(preview, width=200, height=120,
                               bg="#FFFFFF", highlightthickness=1,
                               highlightbackground="#000000"),
            "Accessory": tk.Canvas(preview, width=200, height=120,
                                   bg="#FFFFFF", highlightthickness=1,
                                   highlightbackground="#000000"),
        }

        self.favorite_preview_canvases["TopOrDress"].pack(pady=2)
        self.favorite_preview_canvases["Bottom"].pack(pady=2)
        self.favorite_preview_canvases["Shoes"].pack(pady=2)
        self.favorite_preview_canvases["Accessory"].pack(pady=2)

    # ---------------- CLOSET LOGIC ----------------
    def _add_item(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Please enter an item name.")
            return

        item = ClothingItem(
            name=name,
            category=self.category_var.get(),
            color=self.color_entry.get().strip(),
            vibe=self.vibe_var.get().strip(),
            image_path=self.image_entry.get().strip()
        )
        self.closet.add_item(item)

        # clear fields
        self.name_entry.delete(0, tk.END)
        self.color_entry.delete(0, tk.END)
        self.image_entry.delete(0, tk.END)
        self.selected_index = None
        self.closet_listbox.selection_clear(0, tk.END)

        self._refresh_closet()

    def _on_select_item(self, event):
        selection = self.closet_listbox.curselection()
        if not selection:
            self.selected_index = None
            return

        idx = selection[0]
        self.selected_index = idx
        item = self.closet.items[idx]

        self.category_var.set(item.category)
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, item.name)
        self.color_entry.delete(0, tk.END)
        self.color_entry.insert(0, item.color)
        self.vibe_var.set(item.vibe)
        self.image_entry.delete(0, tk.END)
        self.image_entry.insert(0, item.image_path)

    def _update_item(self):
        if self.selected_index is None:
            messagebox.showwarning("No selection", "Select an item to update.")
            return

        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Please enter an item name.")
            return

        updated = ClothingItem(
            name=name,
            category=self.category_var.get(),
            color=self.color_entry.get().strip(),
            vibe=self.vibe_var.get().strip(),
            image_path=self.image_entry.get().strip()
        )
        self.closet.items[self.selected_index] = updated
        self._refresh_closet()

    def _delete_item(self):
        if self.selected_index is None:
            messagebox.showwarning("No selection", "Select an item to delete.")
            return

        item = self.closet.items[self.selected_index]
        if not messagebox.askyesno("Delete item", f"Remove '{item.name}' from your closet?"):
            return

        del self.closet.items[self.selected_index]
        self.selected_index = None
        self.closet_listbox.selection_clear(0, tk.END)
        self._refresh_closet()

    def _refresh_closet(self):
        self.closet_listbox.delete(0, tk.END)
        for item in self.closet.items:
            self.closet_listbox.insert(tk.END, f"{item.category}: {item}")

    def _save_closet(self):
        save_closet(self.closet)
        messagebox.showinfo("Saved", "Closet saved successfully.")

    # ---------------- TODAY'S OUTFIT + IMAGES ----------------
    def _pick_outfit(self):
        if not self.closet.items:
            messagebox.showwarning("Empty closet", "Add some items to your closet first!")
            return

        outfit = self.closet.random_outfit(
            vibe=self.today_vibe_var.get(),
            include_accessory=self.include_accessory_var.get()
        )

        # text labels
        for cat, lbl in self.outfit_labels.items():
            item = outfit.get(cat)
            lbl.config(text=str(item) if item else "(none)")

        # images
        self._update_outfit_images(outfit)

        self.current_outfit = outfit

    def _update_outfit_images(self, outfit: dict):
        # clear old
        for key in self.outfit_images:
            self.outfit_images[key] = None
        for canvas in self.preview_canvases.values():
            canvas.delete("all")

        top_or_dress_item = outfit.get("Dress") or outfit.get("Top")
        bottom_item = outfit.get("Bottom")
        shoes_item = outfit.get("Shoes")
        accessory_item = outfit.get("Accessory")

        def load_img(item):
            if not item or not item.image_path:
                return None
            if not os.path.exists(item.image_path):
                return None
            try:
                img = Image.open(item.image_path)
                img = img.convert("RGBA")
                img.thumbnail((200, 130))  # fit inside each rectangle
                return ImageTk.PhotoImage(img)
            except Exception:
                return None

        self.outfit_images["TopOrDress"] = load_img(top_or_dress_item)
        self.outfit_images["Bottom"] = load_img(bottom_item)
        self.outfit_images["Shoes"] = load_img(shoes_item)
        self.outfit_images["Accessory"] = load_img(accessory_item)

        placeholders = {
            "TopOrDress": "Top / Dress",
            "Bottom": "Bottom",
            "Shoes": "Shoes",
            "Accessory": "Accessory",
        }

        for key, canvas in self.preview_canvases.items():
            img = self.outfit_images[key]
            if img is not None:
                canvas.create_image(100, 60, image=img)
            else:
                canvas.create_text(
                    80,
                    35,
                    text=placeholders[key],
                    font=("Comic Sans MS", 9),
                    fill="#777777"
                )

    # ---------------- FAVORITES (SAVE + VIEW PANEL) ----------------
    def _save_favorite(self):
        if not hasattr(self, "current_outfit"):
            messagebox.showwarning("No outfit", "Pick an outfit first!")
            return

        name = self.favorite_name_entry.get().strip()
        self.closet.add_favorite(self.current_outfit, name)
        self.favorite_name_entry.delete(0, tk.END)
        self._refresh_favorites()

    def _refresh_favorites(self):
        # rebuild listbox of saved outfits
        self.favorites_listbox.delete(0, tk.END)
        for fav in self.closet.favorites:
            self.favorites_listbox.insert(tk.END, fav.get("label", "Favorite"))

    def _on_select_favorite(self, event):
        selection = self.favorites_listbox.curselection()
        if not selection:
            empty = {
                "Top": None,
                "Bottom": None,
                "Dress": None,
                "Shoes": None,
                "Accessory": None,
            }
            self._update_favorite_preview(empty)
            return

        idx = selection[0]
        fav = self.closet.favorites[idx]
        outfit_data = fav.get("outfit", {})

        # convert dicts back to ClothingItem for preview
        outfit_items = {}
        for cat in ["Top", "Bottom", "Dress", "Shoes", "Accessory"]:
            data = outfit_data.get(cat)
            outfit_items[cat] = ClothingItem.from_dict(data) if data else None

        # update text labels
        for cat, lbl in self.favorite_detail_labels.items():
            item = outfit_items.get(cat)
            lbl.config(text=str(item) if item else "(none)")

        # update stacked images
        self._update_favorite_preview(outfit_items)

    def _update_favorite_preview(self, outfit_items: dict):
        # outfit_items: dict with ClothingItem or None
        for key in self.favorite_images:
            self.favorite_images[key] = None
        for canvas in self.favorite_preview_canvases.values():
            canvas.delete("all")

        top_or_dress_item = outfit_items.get("Dress") or outfit_items.get("Top")
        bottom_item = outfit_items.get("Bottom")
        shoes_item = outfit_items.get("Shoes")
        accessory_item = outfit_items.get("Accessory")

        def load_img(item):
            if not item or not item.image_path:
                return None
            if not os.path.exists(item.image_path):
                return None
            try:
                img = Image.open(item.image_path)
                img = img.convert("RGBA")
                img.thumbnail((200, 130))
                return ImageTk.PhotoImage(img)
            except Exception:
                return None

        self.favorite_images["TopOrDress"] = load_img(top_or_dress_item)
        self.favorite_images["Bottom"] = load_img(bottom_item)
        self.favorite_images["Shoes"] = load_img(shoes_item)
        self.favorite_images["Accessory"] = load_img(accessory_item)

        placeholders = {
            "TopOrDress": "Top / Dress",
            "Bottom": "Bottom",
            "Shoes": "Shoes",
            "Accessory": "Accessory",
        }

        for key, canvas in self.favorite_preview_canvases.items():
            img = self.favorite_images[key]
            if img is not None:
                canvas.create_image(100, 60, image=img)
            else:
                canvas.create_text(
                    70,
                    30,
                    text=placeholders[key],
                    font=("Comic Sans MS", 9),
                    fill="#777777"
                )
