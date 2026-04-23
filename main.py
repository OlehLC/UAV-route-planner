import sys
import tkinter as tk
from controller import Controller
from view import AppView

def on_close():
    root.destroy()
    sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    
    controller = Controller()
    app = AppView(root, controller)
    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()
