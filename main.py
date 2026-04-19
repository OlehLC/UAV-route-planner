import sys
import tkinter as tk
from controller import Controller
from view import AppView

def on_close():
    root.destroy()
    sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    controller = Controller()
    app = AppView(root, controller)
    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()
