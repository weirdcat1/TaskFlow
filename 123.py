import customtkinter as ctk
import sqlite3
from tkinter import messagebox
from datetime import datetime
import hashlib

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def center_window(window, width, height):
    window.update_idletasks()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('todo_app.db')
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.create_default_admin()
        self.add_test_users()
    
    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        self.conn.commit()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_default_admin(self):
        self.cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, role)
            VALUES (?, ?, ?)
        ''', ('admin', self.hash_password('admin123'), 'admin'))
        self.conn.commit()
    
    def add_test_users(self):
        self.cursor.execute('SELECT COUNT(*) FROM users')
        if self.cursor.fetchone()[0] > 1:
            return
        
        test_users = [
            ('admin2', 'admin456', 'admin'),
            ('user1', 'pass123', 'user'),
            ('user2', 'pass123', 'user'),
            ('user3', 'pass123', 'user'),
            ('user4', 'pass123', 'user'),
            ('user5', 'pass123', 'user'),
            ('user6', 'pass123', 'user'),
            ('user7', 'pass123', 'user'),
            ('user8', 'pass123', 'user')
        ]
        
        for username, password, role in test_users:
            try:
                self.cursor.execute('''
                    INSERT INTO users (username, password, role)
                    VALUES (?, ?, ?)
                ''', (username, self.hash_password(password), role))
            except sqlite3.IntegrityError:
                pass
        
        self.conn.commit()
    
    def register_user(self, username, password):
        try:
            self.cursor.execute('''
                INSERT INTO users (username, password, role)
                VALUES (?, ?, 'user')
            ''', (username, self.hash_password(password)))
            self.conn.commit()
            return True, "Регистрация успешна!"
        except sqlite3.IntegrityError:
            return False, "Пользователь с таким именем уже существует!"
    
    def login_user(self, username, password):
        self.cursor.execute('''
            SELECT id, username, role FROM users 
            WHERE username = ? AND password = ?
        ''', (username, self.hash_password(password)))
        return self.cursor.fetchone()
    
    def get_all_users(self):
        self.cursor.execute('SELECT id, username, role, created_at FROM users ORDER BY id')
        return self.cursor.fetchall()
    
    def delete_user(self, user_id):
        self.cursor.execute('DELETE FROM tasks WHERE user_id = ?', (user_id,))
        self.cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        self.conn.commit()
    
    def reset_password(self, user_id, new_password='newpass123'):
        self.cursor.execute('''
            UPDATE users SET password = ? WHERE id = ?
        ''', (self.hash_password(new_password), user_id))
        self.conn.commit()
    
    def get_user_tasks(self, user_id):
        self.cursor.execute('''
            SELECT id, title, description, status, created_at 
            FROM tasks WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        return self.cursor.fetchall()
    
    def add_task(self, user_id, title, description):
        self.cursor.execute('''
            INSERT INTO tasks (user_id, title, description)
            VALUES (?, ?, ?)
        ''', (user_id, title, description))
        self.conn.commit()
    
    def update_task(self, task_id, title, description):
        self.cursor.execute('''
            UPDATE tasks SET title = ?, description = ? WHERE id = ?
        ''', (title, description, task_id))
        self.conn.commit()
    
    def update_task_status(self, task_id, status):
        self.cursor.execute('''
            UPDATE tasks SET status = ? WHERE id = ?
        ''', (status, task_id))
        self.conn.commit()
    
    def delete_task(self, task_id):
        self.cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        self.conn.commit()

class LoginWindow(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("Вход в систему")
        self.geometry("400x500")
        self.resizable(False, False)
        center_window(self, 400, 500)
        
        self.label_title = ctk.CTkLabel(
            self, 
            text="Список задач", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.label_title.pack(pady=20)
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.tab_login = self.tabview.add("Вход")
        self.tab_register = self.tabview.add("Регистрация")
        
        self.create_login_tab()
        self.create_register_tab()
    
    def create_login_tab(self):
        self.login_username = ctk.CTkEntry(
            self.tab_login, 
            placeholder_text="Логин",
            width=250,
            height=40
        )
        self.login_username.pack(pady=10)
        
        self.login_password = ctk.CTkEntry(
            self.tab_login, 
            placeholder_text="Пароль",
            show="*",
            width=250,
            height=40
        )
        self.login_password.pack(pady=10)
        
        self.login_button = ctk.CTkButton(
            self.tab_login,
            text="Войти",
            command=self.login,
            width=250,
            height=40
        )
        self.login_button.pack(pady=20)
    
    def create_register_tab(self):
        self.register_username = ctk.CTkEntry(
            self.tab_register, 
            placeholder_text="Логин",
            width=250,
            height=40
        )
        self.register_username.pack(pady=10)
        
        self.register_password = ctk.CTkEntry(
            self.tab_register, 
            placeholder_text="Пароль",
            show="*",
            width=250,
            height=40
        )
        self.register_password.pack(pady=10)
        
        self.register_confirm = ctk.CTkEntry(
            self.tab_register, 
            placeholder_text="Подтвердите пароль",
            show="*",
            width=250,
            height=40
        )
        self.register_confirm.pack(pady=10)
        
        self.register_button = ctk.CTkButton(
            self.tab_register,
            text="Зарегистрироваться",
            command=self.register,
            width=250,
            height=40
        )
        self.register_button.pack(pady=20)
    
    def login(self):
        username = self.login_username.get()
        password = self.login_password.get()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        
        user = self.db.login_user(username, password)
        if user:
            self.destroy()
            MainApp(user, self.db).mainloop()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль!")
    
    def register(self):
        username = self.register_username.get()
        password = self.register_password.get()
        confirm = self.register_confirm.get()
        
        if not username or not password or not confirm:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        
        if password != confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают!")
            return
        
        if len(password) < 6:
            messagebox.showerror("Ошибка", "Пароль должен быть не менее 6 символов!")
            return
        
        success, message = self.db.register_user(username, password)
        if success:
            messagebox.showinfo("Успех", message)
            self.tabview.set("Вход")
            self.login_username.delete(0, 'end')
            self.login_password.delete(0, 'end')
        else:
            messagebox.showerror("Ошибка", message)

class EditTaskDialog(ctk.CTkToplevel):
    def __init__(self, parent, task_id, current_title, current_description, on_save_callback):
        super().__init__(parent)
        self.task_id = task_id
        self.on_save_callback = on_save_callback
        
        self.title("✏️ Редактирование задачи")
        self.geometry("500x450")
        self.minsize(450, 400)
        self.resizable(True, True)
        
        self.after(10, lambda: center_window(self, 500, 450))
        self.grab_set()
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(self, height=50, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        ctk.CTkLabel(header, text="✏️ Редактирование задачи", font=ctk.CTkFont(size=16, weight="bold")).pack(expand=True)
        
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(main_frame, text="Название задачи", font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.title_entry = ctk.CTkEntry(main_frame, height=40)
        self.title_entry.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.title_entry.insert(0, current_title)
        self.title_entry.focus()
        
        ctk.CTkLabel(main_frame, text="Описание задачи", font=ctk.CTkFont(size=13, weight="bold")).grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.desc_text = ctk.CTkTextbox(main_frame, height=120)
        self.desc_text.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        if current_description:
            self.desc_text.insert("1.0", current_description)
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Сохранить",
            command=self.save,
            height=40,
            fg_color="#27ae60"
        )
        save_btn.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="✖ Отмена",
            command=self.destroy,
            height=40,
            fg_color="#7f8c8d"
        )
        cancel_btn.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
    
    def save(self):
        new_title = self.title_entry.get().strip()
        if not new_title:
            messagebox.showerror("Ошибка", "Введите название задачи!")
            return
        
        new_description = self.desc_text.get("1.0", "end-1c")
        self.on_save_callback(self.task_id, new_title, new_description)
        self.destroy()

class MainApp(ctk.CTk):
    def __init__(self, user, db):
        super().__init__()
        self.user = user
        self.db = db
        self.user_id, self.username, self.role = user
        
        self.title(f"Список задач - {self.username} ({self.role})")
        self.geometry("900x700")
        self.minsize(800, 600)
        center_window(self, 900, 700)
        
        self.setup_ui()
    
    def setup_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.top_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.top_frame.grid(row=0, column=0, sticky="ew")
        self.top_frame.grid_propagate(False)
        self.top_frame.grid_columnconfigure(0, weight=1)
        
        self.user_label = ctk.CTkLabel(
            self.top_frame,
            text=f"👤 {self.username} ({self.role})",
            font=ctk.CTkFont(size=14)
        )
        self.user_label.pack(side="left", padx=20)
        
        self.logout_button = ctk.CTkButton(
            self.top_frame,
            text="🚪 Выйти",
            command=self.logout,
            width=100,
            height=35,
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        self.logout_button.pack(side="right", padx=20)
        
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        if self.role == 'admin':
            self.tabview = ctk.CTkTabview(self.main_frame)
            self.tabview.grid(row=0, column=0, sticky="nsew")
            
            self.tab_users = self.tabview.add("👥 Пользователи")
            self.tab_tasks = self.tabview.add("📋 Мои задачи")
            
            self.create_users_tab()
            self.create_tasks_tab()
        else:
            self.create_tasks_tab()
    
    def create_users_tab(self):
        self.tab_users.grid_columnconfigure(0, weight=1)
        self.tab_users.grid_rowconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(
            self.tab_users,
            text="Управление пользователями",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_label.grid(row=0, column=0, pady=10)
        
        self.users_frame = ctk.CTkScrollableFrame(self.tab_users)
        self.users_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.users_frame.grid_columnconfigure(0, weight=1)
        
        self.load_users()
    
    def load_users(self):
        for widget in self.users_frame.winfo_children():
            widget.destroy()
        
        for user in self.db.get_all_users():
            user_id, username, role, _ = user
            
            user_card = ctk.CTkFrame(self.users_frame)
            user_card.pack(pady=5, padx=5, fill="x")
            user_card.grid_columnconfigure(1, weight=1)
            
            role_icon = "👑" if role == "admin" else "👤"
            icon_label = ctk.CTkLabel(user_card, text=role_icon, font=ctk.CTkFont(size=20))
            icon_label.grid(row=0, column=0, padx=15, pady=10)
            
            info_text = f"{username} ({role})"
            if user_id == self.user_id:
                info_text += " [Вы]"
            
            info_label = ctk.CTkLabel(user_card, text=info_text, font=ctk.CTkFont(size=13))
            info_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")
            
            if user_id != self.user_id:
                btn_frame = ctk.CTkFrame(user_card, fg_color="transparent")
                btn_frame.grid(row=0, column=2, padx=10, pady=5)
                
                reset_btn = ctk.CTkButton(
                    btn_frame,
                    text="🔄 Сброс",
                    command=lambda uid=user_id: self.reset_user_password(uid),
                    width=90,
                    height=32,
                    fg_color="#f39c12"
                )
                reset_btn.pack(side="left", padx=3)
                
                delete_btn = ctk.CTkButton(
                    btn_frame,
                    text="🗑️",
                    command=lambda uid=user_id, uname=username: self.delete_user_confirm(uid, uname),
                    width=50,
                    height=32,
                    fg_color="#e74c3c"
                )
                delete_btn.pack(side="left", padx=3)
    
    def delete_user_confirm(self, user_id, username):
        if messagebox.askyesno("Подтверждение", f"Удалить пользователя {username}?"):
            self.db.delete_user(user_id)
            messagebox.showinfo("Успех", f"Пользователь {username} удален!")
            self.load_users()
    
    def reset_user_password(self, user_id):
        if messagebox.askyesno("Подтверждение", "Сбросить пароль на 'newpass123'?"):
            self.db.reset_password(user_id)
            messagebox.showinfo("Успех", "Пароль сброшен на 'newpass123'")
    
    def create_tasks_tab(self):
        container = self.tab_tasks if hasattr(self, 'tabview') else self.main_frame
        
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=0)
        container.grid_rowconfigure(1, weight=0)
        container.grid_rowconfigure(2, weight=1)
        
        header_label = ctk.CTkLabel(
            container,
            text="📋 Мои задачи",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_label.grid(row=0, column=0, pady=10)
        
        add_frame = ctk.CTkFrame(container)
        add_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        add_frame.grid_columnconfigure(0, weight=2)
        add_frame.grid_columnconfigure(1, weight=3)
        add_frame.grid_columnconfigure(2, weight=0)
        
        self.task_title = ctk.CTkEntry(
            add_frame,
            placeholder_text="Название задачи",
            height=40
        )
        self.task_title.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        
        self.task_desc = ctk.CTkEntry(
            add_frame,
            placeholder_text="Описание задачи",
            height=40
        )
        self.task_desc.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        add_btn = ctk.CTkButton(
            add_frame,
            text="➕ Добавить",
            command=self.add_task,
            width=100,
            height=40,
            fg_color="#27ae60"
        )
        add_btn.grid(row=0, column=2, padx=5, pady=10)
        
        self.tasks_frame = ctk.CTkScrollableFrame(container)
        self.tasks_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.tasks_frame.grid_columnconfigure(0, weight=1)
        
        self.load_tasks()
    
    def add_task(self):
        title = self.task_title.get().strip()
        description = self.task_desc.get().strip()
        
        if not title:
            messagebox.showerror("Ошибка", "Введите название задачи!")
            return
        
        self.db.add_task(self.user_id, title, description)
        self.task_title.delete(0, 'end')
        self.task_desc.delete(0, 'end')
        self.load_tasks()
    
    def edit_task(self, task_id, current_title, current_description):
        EditTaskDialog(self, task_id, current_title, current_description, self.save_task_changes)
    
    def save_task_changes(self, task_id, new_title, new_description):
        self.db.update_task(task_id, new_title, new_description)
        self.load_tasks()
        messagebox.showinfo("Успех", "Задача обновлена!")
    
    def load_tasks(self):
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()
        
        tasks = self.db.get_user_tasks(self.user_id)
        
        if not tasks:
            empty_label = ctk.CTkLabel(
                self.tasks_frame,
                text="📭 У вас пока нет задач",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            empty_label.pack(expand=True, pady=50)
            return
        
        for task in tasks:
            task_id, title, description, status, created_at = task
            
            task_card = ctk.CTkFrame(self.tasks_frame)
            task_card.pack(pady=5, padx=5, fill="x")
            task_card.grid_columnconfigure(1, weight=1)
            
            status_text = "✓" if status == "completed" else "○"
            status_color = "#27ae60" if status == "completed" else "#f39c12"
            
            status_label = ctk.CTkLabel(
                task_card,
                text=status_text,
                font=ctk.CTkFont(size=20),
                text_color=status_color
            )
            status_label.grid(row=0, column=0, padx=15, pady=15)
            
            info_frame = ctk.CTkFrame(task_card, fg_color="transparent")
            info_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
            info_frame.grid_columnconfigure(0, weight=1)
            
            title_label = ctk.CTkLabel(
                info_frame,
                text=title,
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            title_label.grid(row=0, column=0, sticky="ew", pady=(0, 3))
            
            if description:
                desc_label = ctk.CTkLabel(
                    info_frame,
                    text=description,
                    font=ctk.CTkFont(size=11),
                    text_color="gray",
                    anchor="w"
                )
                desc_label.grid(row=1, column=0, sticky="ew")
            
            date_label = ctk.CTkLabel(
                info_frame,
                text=f"📅 {created_at[:10]}",
                font=ctk.CTkFont(size=10),
                text_color="gray",
                anchor="w"
            )
            date_label.grid(row=2, column=0, sticky="ew", pady=(3, 0))
            
            btn_frame = ctk.CTkFrame(task_card, fg_color="transparent")
            btn_frame.grid(row=0, column=2, padx=10, pady=5)
            
            edit_btn = ctk.CTkButton(
                btn_frame,
                text="✏️",
                command=lambda tid=task_id, ttl=title, desc=description: self.edit_task(tid, ttl, desc),
                width=40,
                height=32,
                fg_color="#3498db"
            )
            edit_btn.pack(side="left", padx=2)
            
            if status == "active":
                complete_btn = ctk.CTkButton(
                    btn_frame,
                    text="✓",
                    command=lambda tid=task_id: self.complete_task(tid),
                    width=40,
                    height=32,
                    fg_color="#27ae60"
                )
                complete_btn.pack(side="left", padx=2)
            
            delete_btn = ctk.CTkButton(
                btn_frame,
                text="🗑️",
                command=lambda tid=task_id: self.delete_task(tid),
                width=40,
                height=32,
                fg_color="#e74c3c"
            )
            delete_btn.pack(side="left", padx=2)
    
    def complete_task(self, task_id):
        self.db.update_task_status(task_id, "completed")
        self.load_tasks()
        messagebox.showinfo("Успех", "Задача завершена!")
    
    def delete_task(self, task_id):
        if messagebox.askyesno("Подтверждение", "Удалить задачу?"):
            self.db.delete_task(task_id)
            self.load_tasks()
    
    def logout(self):
        self.destroy()
        LoginWindow(self.db).mainloop()

if __name__ == "__main__":
    db = Database()
    LoginWindow(db).mainloop()