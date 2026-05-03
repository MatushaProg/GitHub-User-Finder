import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from threading import Thread

# Файл для хранения избранных пользователей
FAVORITES_FILE = "favorites.json"

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("900x600")
        self.root.resizable(True, True)

        # Загрузка избранных
        self.favorites = self.load_favorites()

        # Переменная для хранения текущих результатов поиска (список словарей)
        self.search_results = []

        # Создание интерфейса
        self.create_widgets()

        # Обновление списка избранных
        self.refresh_favorites_list()

    def create_widgets(self):
        # Рамка поиска
        search_frame = ttk.LabelFrame(self.root, text="Поиск пользователей GitHub", padding=10)
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Логин или имя:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)
        self.search_btn = ttk.Button(search_frame, text="Найти", command=self.search_users_thread)
        self.search_btn.grid(row=0, column=2, padx=5, pady=5)

        # Рамка результатов поиска
        results_frame = ttk.LabelFrame(self.root, text="Результаты поиска", padding=10)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Таблица результатов
        columns = ("login", "id", "url")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=10)
        self.results_tree.heading("login", text="Логин")
        self.results_tree.heading("id", text="ID")
        self.results_tree.heading("url", text="URL профиля")
        self.results_tree.column("login", width=150)
        self.results_tree.column("id", width=80)
        self.results_tree.column("url", width=300)

        scroll_y = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scroll_y.set)
        self.results_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Кнопка добавления в избранное
        add_fav_btn = ttk.Button(results_frame, text="Добавить выбранного в избранное", command=self.add_to_favorites)
        add_fav_btn.pack(pady=5)

        # Рамка избранного
        fav_frame = ttk.LabelFrame(self.root, text="Избранные пользователи", padding=10)
        fav_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Таблица избранных
        fav_columns = ("login", "id", "url")
        self.fav_tree = ttk.Treeview(fav_frame, columns=fav_columns, show="headings", height=6)
        self.fav_tree.heading("login", text="Логин")
        self.fav_tree.heading("id", text="ID")
        self.fav_tree.heading("url", text="URL профиля")
        self.fav_tree.column("login", width=150)
        self.fav_tree.column("id", width=80)
        self.fav_tree.column("url", width=300)

        fav_scroll = ttk.Scrollbar(fav_frame, orient="vertical", command=self.fav_tree.yview)
        self.fav_tree.configure(yscrollcommand=fav_scroll.set)
        self.fav_tree.pack(side="left", fill="both", expand=True)
        fav_scroll.pack(side="right", fill="y")

        # Кнопка удаления из избранного
        remove_fav_btn = ttk.Button(fav_frame, text="Удалить выбранного из избранного", command=self.remove_from_favorites)
        remove_fav_btn.pack(pady=5)

        # Статусная строка
        self.status_label = ttk.Label(self.root, text="Готов", relief="sunken", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=5)

    def search_users_thread(self):
        """Запуск поиска в отдельном потоке, чтобы не блокировать GUI."""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Предупреждение", "Введите логин или имя пользователя для поиска.")
            return

        self.search_btn.config(state="disabled", text="Поиск...")
        self.status_label.config(text="Выполняется поиск...")
        thread = Thread(target=self.search_users, args=(query,))
        thread.daemon = True
        thread.start()

    def search_users(self, query):
        """Выполняет запрос к GitHub API и обновляет таблицу результатов."""
        url = f"https://api.github.com/search/users?q={query}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])

            # Формируем список результатов
            self.search_results = []
            for user in items:
                self.search_results.append({
                    "login": user["login"],
                    "id": user["id"],
                    "url": user["html_url"]
                })

            # Обновляем таблицу в главном потоке
            self.root.after(0, self.update_results_table)
            self.root.after(0, lambda: self.status_label.config(text=f"Найдено пользователей: {len(self.search_results)}"))
        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка сети", f"Не удалось выполнить запрос:\n{e}"))
            self.root.after(0, lambda: self.status_label.config(text="Ошибка поиска"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Неизвестная ошибка:\n{e}"))
            self.root.after(0, lambda: self.status_label.config(text="Ошибка"))
        finally:
            self.root.after(0, lambda: self.search_btn.config(state="normal", text="Найти"))

    def update_results_table(self):
        """Отображает self.search_results в Treeview."""
        # Очистка текущих данных
        for row in self.results_tree.get_children():
            self.results_tree.delete(row)

        for user in self.search_results:
            self.results_tree.insert("", tk.END, values=(user["login"], user["id"], user["url"]))

    def add_to_favorites(self):
        """Добавляет выбранного пользователя из результатов в избранное."""
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите пользователя из результатов поиска.")
            return

        # Берем первый выбранный элемент
        item = self.results_tree.item(selected[0])
        values = item["values"]
        # values = (login, id, url)
        login, user_id, url = values

        # Проверяем, нет ли уже такого пользователя в избранном
        for fav in self.favorites:
            if fav["id"] == user_id:
                messagebox.showinfo("Информация", f"Пользователь {login} уже в избранном.")
                return

        new_fav = {"login": login, "id": user_id, "url": url}
        self.favorites.append(new_fav)
        self.save_favorites()
        self.refresh_favorites_list()
        self.status_label.config(text=f"{login} добавлен в избранное")

    def remove_from_favorites(self):
        """Удаляет выбранного пользователя из избранного."""
        selected = self.fav_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите пользователя в списке избранного.")
            return

        item = self.fav_tree.item(selected[0])
        values = item["values"]
        login, user_id, url = values

        # Удаляем по id
        self.favorites = [fav for fav in self.favorites if fav["id"] != user_id]
        self.save_favorites()
        self.refresh_favorites_list()
        self.status_label.config(text=f"{login} удалён из избранного")

    def refresh_favorites_list(self):
        """Обновляет таблицу избранных пользователей."""
        for row in self.fav_tree.get_children():
            self.fav_tree.delete(row)

        for fav in self.favorites:
            self.fav_tree.insert("", tk.END, values=(fav["login"], fav["id"], fav["url"]))

    def load_favorites(self):
        """Загружает избранных из JSON-файла."""
        if os.path.exists(FAVORITES_FILE):
            try:
                with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_favorites(self):
        """Сохраняет избранных в JSON-файл."""
        try:
            with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить избранное:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()