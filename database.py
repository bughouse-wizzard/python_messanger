import sqlite3

class DatabaseManager:
    def __init__(self, db_file_name):
        self.db_file_name = db_file_name
        self.connection = sqlite3.connect(self.db_file_name, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.initialize_tables()

    def initialize_tables(self):
        self.initial_users()
        self.initial_chats()
        self.initial_messages()
        self.initial_comments()

    def initial_users(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY,
                login TEXT,
                password_hash TEXT,
                salt TEXT)
        """)
        self.connection.commit()

    def initial_chats(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Chats (
                id INTEGER PRIMARY KEY,
                name TEXT)
        """)
        self.connection.commit()

    def initial_messages(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Messages (
                id INTEGER PRIMARY KEY,
                chat_id INTEGER,
                message TEXT,
                user_id INTEGER,
                likes JSON DEFAULT NULL,
                time DATETIME)
        """)
        self.connection.commit()

    def initial_comments(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Comments (
                id INTEGER PRIMARY KEY,
                message_id INTEGER,
                user_id INTEGER,
                comment TEXT,
                time DATETIME)
        """)
        self.connection.commit()

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()
