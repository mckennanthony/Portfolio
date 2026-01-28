# main.py
import tkinter as tk
from app_gui import OutfitApp

def main():
    root = tk.Tk()
    app = OutfitApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
