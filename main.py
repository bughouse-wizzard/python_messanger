from tkinter import Tk
from passwords import PasswordManager

if __name__ == "__main__":
    root = Tk()
    app = PasswordManager(root)
    root.mainloop()