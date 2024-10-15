from tkinter import *
from tkinter import messagebox
import uuid
import hashlib
from database import DatabaseManager
from Messenger import Messenger

db = DatabaseManager('users.db')

class PasswordManager:
    def __init__(self, root):
        self.root = root
        self.root.title('Passwords')
        self.center_window(250, 150)

        self.label1 = Label(root, text='Login:', anchor='center')
        self.label2 = Label(root, text='Password:', anchor='center')
        self.entry1 = Entry(root)
        self.entry2 = Entry(root, show='*')
        self.signup = Button(root, text='Sign up', command=self.up)
        self.signin = Button(root, text='Sign in', command=self.in_)
        self.ok = Button(root, text='Ok', command=self.safe)
        self.ok_in = Button(root, text='Ok', command=self.check)
        self.exit = Button(root, text='Exit', command=self.cls)

        self.signup.pack()
        self.signin.pack()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def hash_password(self, password, salt):
        return hashlib.sha256((salt.encode() + password.encode())).hexdigest()

    def check_password(self, hashed_password, user_password, salt):
        return hashed_password == self.hash_password(user_password, salt)

    def up(self):
        self.signup.pack_forget()
        self.signin.pack_forget()
        self.label1.pack()
        self.entry1.pack()
        self.label2.pack()
        self.entry2.pack()
        self.ok.pack()

    def in_(self):
        self.up()
        self.ok.pack_forget()
        self.ok_in.pack()
        self.exit.pack()

    def safe(self):
        salt = uuid.uuid4().hex
        db.cursor.execute("INSERT INTO Users (login, password_hash, salt) VALUES (?, ?, ?)", (self.entry1.get(), self.hash_password(self.entry2.get(), salt), salt))
        db.commit()
        self.label1.pack_forget()
        self.entry1.pack_forget()
        self.label2.pack_forget()
        self.entry2.pack_forget()
        self.ok.pack_forget()
        self.signup.pack()
        self.signin.pack()
        self.entry1.delete(0, END)
        self.entry2.delete(0, END)
        messagebox.showinfo("Saved", "Credentials saved successfully")

    def cls(self):
        self.label1.pack_forget()
        self.label2.pack_forget()
        self.entry1.pack_forget()
        self.entry2.pack_forget()
        self.ok_in.pack_forget()
        self.signup.pack()
        self.signin.pack()
        self.entry1.delete(0, END)
        self.entry2.delete(0, END)
        self.exit.pack_forget()

    def check(self):
        username = self.entry1.get()
        password = self.entry2.get()
        for user_id, user, hashed_password, salt in db.cursor.execute("SELECT user_id, login, password_hash, salt FROM Users").fetchall():
            if user == username:
                if self.check_password(hashed_password, password, salt):
                    messagebox.showinfo("Success", "Login successful")
                    self.root.destroy()
                    self.open_messanger(user_id, username)
                    return
                else:
                    messagebox.showerror("Error", "Incorrect password")
                    return
        messagebox.showerror("Error", "User not found")

    def open_messanger(self, user_id, username):
        root = Tk()
        app = Messenger(root, user_id, username)
        root.mainloop()
