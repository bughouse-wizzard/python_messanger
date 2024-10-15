from tkinter import *
from tkinter import messagebox
from tkinter.simpledialog import askstring
import datetime
from database import DatabaseManager
from message_verify import MessageChecker
import json

db = DatabaseManager('users.db')

class Messenger:
    def __init__(self, root, user_id, username):
        self.root = root
        self.user_id = user_id
        self.username = username
        self.root.title('Messenger')
        self.center_window(1200, 600)

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

        # Setting up a canvas for scrolling messages
        self.canvas = Canvas(self.right_frame)
        self.scroll_y = Scrollbar(self.right_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_y.grid(row=0, column=1, sticky='ns')
        
        # Frame inside canvas to hold messages and make it scrollable
        self.messages_frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.messages_frame, anchor='nw')
        self.canvas.config(yscrollcommand=self.scroll_y.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")

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

        self.messages_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def newchat(self):
        chatname = askstring('New Chat', 'Enter chat name')
        if chatname:
            try:
                db.cursor.execute("INSERT INTO Chats (name) VALUES (?)", (chatname,))
                db.commit()
                messagebox.showinfo('Chat Adding', 'Success')
                self.refresh_chat_list()
            except Exception as e:
                messagebox.showerror('Database Error', str(e))
        else:
            messagebox.showwarning('Chat Adding', 'Chat name cannot be empty')

    def refresh_chat_list(self):
        self.chat_listbox.delete(0, END)
        self.chat_ids = []
        try:
            chat_names = db.cursor.execute("SELECT name, id FROM Chats").fetchall()
            for chat_name, chat_id in chat_names:
                self.chat_listbox.insert(END, chat_name)
                self.chat_ids.append(chat_id)
        except Exception as e:
            messagebox.showerror('Database Error', str(e))

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
            for widget in self.messages_frame.winfo_children():
                widget.destroy()
            self.message_entry.config(state='disabled')
            self.send_button.config(state='disabled')

    def load_messages(self):
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        try:
            messages = db.cursor.execute("""
                SELECT Messages.message, Users.login, Messages.time, Messages.id
                FROM Messages 
                JOIN Users ON Messages.user_id = Users.user_id 
                WHERE Messages.chat_id = ? 
                ORDER BY Messages.time
            """, (self.current_chat_id,)).fetchall()
            row = 0
            for message_text, sender_login, message_time, message_id in messages:
                likes = self.get_likes_count(message_id)
                display_text = f": {likes} | {message_time[:-7]} {sender_login}: {message_text}"

                message_label = Label(self.messages_frame, text=display_text, anchor="w", justify=LEFT)
                message_label.grid(row=row, column=2, sticky="w")
                
                like_button = Button(self.messages_frame, text='👍', command=lambda mid=message_id: self.like_message(mid, self.user_id))
                like_button.grid(row=row, column=1, sticky="e")
                
                comment_button = Button(self.messages_frame, text='🗨', command=lambda mid=message_id: self.comment_message(mid))
                comment_button.grid(row=row, column=0, sticky="e")

                row += 1

                comments = self.get_comments(message_id)
                for comment in comments:
                    comment_label = Label(self.messages_frame, text=f"\t{comment['user']}: {comment['text']}", anchor="w", justify=LEFT)
                    comment_label.grid(row=row, column=2, columnspan=3, sticky='w')
                    row += 1

            self.canvas.update_idletasks()
            self.canvas.yview_moveto(1)
        except Exception as e:
            messagebox.showerror('Database Error', str(e))

    def like_message(self, message_id, user_id):
        try:
            db.cursor.execute("SELECT likes FROM Messages WHERE id = ?", (message_id,))
            result = db.cursor.fetchone()
            
            likes = json.loads(result[0]) if result[0] else []
            if user_id in likes:
                likes.remove(user_id)
            else:
                likes.append(user_id)
            db.cursor.execute("UPDATE Messages SET likes = ? WHERE id = ?", (json.dumps(likes), message_id))
            db.commit()
            self.load_messages()
        except Exception as e:
            messagebox.showerror('Database Error', str(e))

    def get_likes_count(self, message_id):
        try:
            db.cursor.execute("SELECT likes FROM Messages WHERE id = ?", (message_id,))
            result = db.cursor.fetchone()
            if result is None:
                return 0
            likes = json.loads(result[0]) if result[0] else []
            return len(likes)
        except Exception as e:
            messagebox.showerror('Database Error', str(e))
            return 0

    def get_comments(self, message_id):
        try:
            comments = db.cursor.execute("""
                SELECT Comments.comment, Users.login
                FROM Comments 
                JOIN Users ON Comments.user_id = Users.user_id 
                WHERE Comments.message_id = ? 
                ORDER BY Comments.time
            """, (message_id,)).fetchall()
            return [{'text': comment_text, 'user': user_login} for comment_text, user_login in comments]
        except Exception as e:
            messagebox.showerror('Database Error', str(e))
            return []

    def comment_message(self, message_id):
        comment_text = askstring("Add Comment", "Enter your comment:")
        if comment_text:
            if MessageChecker.check_message(comment_text):
                try:
                    current_time = datetime.datetime.now()
                    db.cursor.execute("INSERT INTO Comments (message_id, comment, user_id, time) VALUES (?, ?, ?, ?)",
                                    (message_id, comment_text, self.user_id, current_time))
                    db.commit()
                    messagebox.showinfo("Comment", "Comment added successfully")
                    self.load_messages()
                except Exception as e:
                    messagebox.showerror('Database Error', str(e))
            else:
                messagebox.showwarning("Warning", "Comment contains forbidden words")
        else:
            messagebox.showwarning("Warning", "Comment cannot be empty")

    def send_message(self):
        message_text = self.message_entry.get()
        if message_text.strip():
            if MessageChecker.check_message(message_text):
                try:
                    current_time = datetime.datetime.now()
                    db.cursor.execute("INSERT INTO Messages (chat_id, message, user_id, time) VALUES (?, ?, ?, ?)",
                                (self.current_chat_id, message_text, self.user_id, current_time))
                    db.commit()
                    self.message_entry.delete(0, END)
                    self.load_messages()
                except Exception as e:
                    messagebox.showerror('Database Error', str(e))
            else:
                messagebox.showwarning("Warning", "Message contains forbidden words")
        else:
            messagebox.showwarning("Warning", "Cannot send empty message")

    def __del__(self):
        db.close()