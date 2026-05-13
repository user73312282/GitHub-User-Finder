import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os

# --- Настройки ---
API_URL = "https://api.github.com/users/"
FAVORITES_FILE = "favorites.json"
GITIGNORE_CONTENT = """# Python
__pycache__/
*.py[cod]
*$py.class

# OS generated files
.DS_Store
Thumbs.db
"""
README_CONTENT = """# GitHub User Finder

## Автор: [Ваше Имя Фамилия]
## Описание:
Графическое приложение на Python (Tkinter) для поиска пользователей на GitHub с помощью официального API. 
Позволяет сохранять понравившихся пользователей в избранное (файл `favorites.json`).

## Как использовать:
1.  Введите логин пользователя в поле.
2.  Нажмите "Поиск".
3.  Нажмите "В избранное", чтобы сохранить.
"""

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        # Создаем необходимые файлы, если их нет
        self.setup_project_files()
        
        # Загрузка избранного
        self.favorites = self.load_favorites()

        # --- Верхняя панель: Поле ввода и кнопка ---
        top_frame = tk.Frame(root)
        top_frame.pack(pady=10, padx=20, fill='x')
        
        self.entry_username = ttk.Entry(top_frame, width=50)
        self.entry_username.pack(side='left', expand=True, fill='x')
        
        btn_search = ttk.Button(top_frame, text="Поиск", command=self.search_user)
        btn_search.pack(side='left', padx=5)

        # --- Дерево результатов (Treeview) ---
        self.frame_results = tk.Frame(root)
        self.frame_results.pack(pady=10, padx=20, fill='both', expand=True)
        
        columns = ("login", "name", "url")
        self.tree = ttk.Treeview(self.frame_results, columns=columns, show="headings", height=15)
        
        self.tree.heading("login", text="Логин")
        self.tree.heading("name", text="Имя")
        self.tree.heading("url", text="Профиль")
        
        self.tree.column("login", width=180)
        self.tree.column("name", width=250)
        self.tree.column("url", width=300)
        
        self.tree.pack(side='left', fill='both', expand=True)
        
        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(self.frame_results, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def setup_project_files(self):
        """Создает .gitignore и README.md при первом запуске."""
        if not os.path.exists(".gitignore"):
            with open(".gitignore", "w", encoding="utf-8") as f:
                f.write(GITIGNORE_CONTENT)
            print("Файл .gitignore создан.")
            
        if not os.path.exists("README.md"):
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(README_CONTENT)
            print("Файл README.md создан.")
            
    def load_favorites(self):
        """Загружает избранных пользователей из JSON."""
        if os.path.exists(FAVORITES_FILE):
            try:
                with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_favorites(self):
        """Сохраняет избранных пользователей в JSON."""
        with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=4)

    def search_user(self):
        """Обрабатывает поиск пользователя."""
        username = self.entry_username.get().strip()
        
        # Проверка на пустое поле
        if not username:
            messagebox.showwarning("Ошибка", "Поле поиска не должно быть пустым!")
            return

        try:
            response = requests.get(API_URL + username, timeout=5)
            response.raise_for_status() # Проверка на ошибки HTTP (404 и др.)
            
            user_data = response.json()
            
            # Очистка таблицы перед выводом нового результата
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Вставка данных пользователя в таблицу
            self.tree.insert("", "end", values=(
                user_data.get('login'),
                user_data.get('name') or "Не указано",
                user_data.get('html_url')
            ))
            
            # Добавляем кнопку "В избранное" в последнюю строку
            last_item_id = self.tree.get_children()[-1]
            
            # Создаем кнопку и привязываем к ней функцию с передачей данных пользователя
            btn_fav = ttk.Button(self.frame_results, text="В избранное", 
                                command=lambda u=user_data: self.add_to_favorites(u))
            
            # Вставляем пустую строку для кнопки в Treeview и помечаем её тегом
            self.tree.insert("", "end", iid=f"btn_{last_item_id}", values=("","",""), tags=("button_row",))
            
            # Функция для правильного позиционирования кнопки внутри ячейки Treeview
            def on_configure(event):
                x, y, w, h = self.tree.bbox(f"btn_{last_item_id}", column="#0")
                btn_fav.place(x=w-120, y=h/2-12, anchor="ne", width=100)
            
            self.tree.bind("<Configure>", on_configure)
            
            messagebox.showinfo("Успех", f"Пользователь {username} найден!")

        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                messagebox.showerror("Ошибка", f"Пользователь {username} не найден.")
            else:
                messagebox.showerror("Ошибка API", f"Код ошибки: {response.status_code}")
                
    def add_to_favorites(self, user_data):
        """Добавляет пользователя в избранное."""
        user_login = user_data.get('login')
        
        if not user_login:
            return

        # Проверка на дубликаты в избранном
        if any(fav.get('login') == user_login for fav in self.favorites):
            messagebox.showinfo("Информация", f"{user_login} уже в избранном!")
            return

        user_to_save = {
            "login": user_login,
            "html_url": user_data.get('html_url'),
            "name": user_data.get('name')
        }
        
        self.favorites.append(user_to_save)
        self.save_favorites()
        
        messagebox.showinfo("Успех", f"{user_login} добавлен в избранное!")


if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()
