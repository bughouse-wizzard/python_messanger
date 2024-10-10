import sqlite3
from tkinter import *
from tkinter import messagebox
from tkinter.simpledialog import askstring
import uuid
import hashlib
import datetime

sql_file_name = "users.db"
sql = sqlite3.connect(sql_file_name, check_same_thread=False)
cursor = sql.cursor()

def initial_users():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY,
            login TEXT,
            password_hash TEXT,
            salt TEXT)
    """)
    sql.commit()
    
def initial_chats():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Chats (
            id INTEGER PRIMARY KEY,
            name TEXT)
    """)
    sql.commit()

def initial_messages():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Messages (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            message TEXT,
            user_id INTEGER,
            time DATETIME)
    """)
    sql.commit()

initial_users()
initial_chats()
initial_messages()
sql.close()

sql = sqlite3.connect(sql_file_name, check_same_thread=False)
cursor = sql.cursor()

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
        cursor.execute("INSERT INTO Users (login, password_hash, salt) VALUES (?, ?, ?)", (self.entry1.get(), self.hash_password(self.entry2.get(), salt), salt))
        sql.commit()
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
        for user_id, user, hashed_password, salt in cursor.execute("SELECT user_id, login, password_hash, salt FROM Users").fetchall():
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
        app = Messanger(root, user_id, username)
        root.mainloop()

class Messanger:
    def __init__(self, root, user_id, username):
        self.root = root
        self.user_id = user_id
        self.username = username
        self.root.title('Messenger')
        self.center_window(700, 500)

        self.current_chat_id = None

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.left_frame = Frame(root)
        self.left_frame.grid(row=0, column=0, sticky='ns')
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        self.right_frame = Frame(root)
        self.right_frame.grid(row=0, column=1, sticky='nsew')
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.button = Button(self.left_frame, text='New Chat', command=self.newchat)
        self.button.grid(row=1, column=0, padx=10, pady=10)

        self.root.bind('<Return>', lambda event: self.send_message())

        self.chat_listbox = Listbox(self.left_frame)
        self.chat_listbox.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        self.scrollbar = Scrollbar(self.left_frame, orient=VERTICAL)
        self.scrollbar.config(command=self.chat_listbox.yview)
        self.chat_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=1, sticky='ns')

        self.chat_listbox.bind('<<ListboxSelect>>', self.open_chat)

        self.messages_frame = Frame(self.right_frame)
        self.messages_frame.grid(row=0, column=0, sticky='nsew')
        self.messages_frame.grid_rowconfigure(0, weight=1)
        self.messages_frame.grid_columnconfigure(0, weight=1)

        self.messages_listbox = Listbox(self.messages_frame)
        self.messages_listbox.grid(row=0, column=0, sticky='nsew')

        self.messages_scrollbar = Scrollbar(self.messages_frame, orient=VERTICAL)
        self.messages_scrollbar.config(command=self.messages_listbox.yview)
        self.messages_listbox.config(yscrollcommand=self.messages_scrollbar.set)
        self.messages_scrollbar.grid(row=0, column=1, sticky='ns')

        self.input_frame = Frame(self.right_frame)
        self.input_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = Entry(self.input_frame)
        self.message_entry.grid(row=0, column=0, sticky='ew')

        self.send_button = Button(self.input_frame, text='Send', command=self.send_message)
        self.send_button.grid(row=0, column=1)

        self.message_entry.config(state='disabled')
        self.send_button.config(state='disabled')

        self.chat_ids = []

        self.refresh_chat_list()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def newchat(self):
        chatname = askstring('New Chat', 'Enter chat name')
        if chatname:
            cursor.execute("INSERT INTO Chats (name) VALUES (?)", (chatname,))
            sql.commit()
            messagebox.showinfo('Chat Adding', 'Success')
            self.refresh_chat_list()
        else:
            messagebox.showwarning('Chat Adding', 'Chat name cannot be empty')

    def refresh_chat_list(self):
        self.chat_listbox.delete(0, END)
        self.chat_ids = []
        chat_names = cursor.execute("SELECT name, id FROM Chats").fetchall()
        for chat_name, chat_id in chat_names:
            self.chat_listbox.insert(END, chat_name)
            self.chat_ids.append(chat_id)

    def open_chat(self, event):
        selection = self.chat_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_chat_id = self.chat_ids[index]
            self.load_messages()
            self.message_entry.config(state='normal')
            self.send_button.config(state='normal')
        else:
            self.current_chat_id = None
            self.messages_listbox.delete(0, END)
            self.message_entry.config(state='disabled')
            self.send_button.config(state='disabled')

    def load_messages(self):
        self.messages_listbox.delete(0, END)
        messages = cursor.execute("""
            SELECT Messages.message, Users.login 
            FROM Messages 
            JOIN Users ON Messages.user_id = Users.user_id 
            WHERE Messages.chat_id = ? 
            ORDER BY Messages.time
        """, (self.current_chat_id,)).fetchall()
        for message_text, sender_login in messages:
            display_text = f"{sender_login}: {message_text}"
            self.messages_listbox.insert(END, display_text)
        self.messages_listbox.see(END)

    def send_message(self):
        message_text = self.message_entry.get()
        if message_text.strip():
            current_time = datetime.datetime.now()
            cursor.execute("INSERT INTO Messages (chat_id, message, user_id, time) VALUES (?, ?, ?, ?)",
                           (self.current_chat_id, message_text, self.user_id, current_time))
            sql.commit()
            self.message_entry.delete(0, END)
            self.load_messages()
        else:
            messagebox.showwarning("Warning", "Cannot send empty message")

if __name__ == "__main__":
    root = Tk()
    app = PasswordManager(root)
    root.mainloop()