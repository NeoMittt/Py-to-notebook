import sys, json, os
from pathlib import Path
from datetime import datetime

# Пытаемся импортировать tkinter, при ошибке используем консольный ввод
try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TK = True
except ImportError:
    HAS_TK = False

def main():
    if HAS_TK:
        root = tk.Tk()
        root.withdraw()
        folder = filedialog.askdirectory(title="Выберите папку с .py файлами")
    else:
        folder = input("Введите путь к папке: ").strip()
        
    if not folder:
        sys.exit("Папка не выбрана. Выход.")
        
    base_dir = Path(folder).resolve()
    
    # Выбор критерия сортировки
    print("\nКритерий сортировки:\n1 - путь/имя (по умолчанию)\n2 - дата изменения\n3 - дата создания\n4 - размер файла")
    c_in = input("Выберите критерий (1-4): ").strip()
    crit = c_in if c_in in ('1', '2', '3', '4') else '1'
    crit_names = {'1': 'путь/имя', '2': 'дата изменения', '3': 'дата создания', '4': 'размер файла'}
    
    # Выбор направления сортировки
    print("\nНаправление сортировки:\n1 - по возрастанию (по умолчанию)\n2 - по убыванию")
    d_in = input("Выберите направление (1-2): ").strip()
    is_desc = (d_in == '2')
    dir_name = "по убыванию ↓" if is_desc else "по возрастанию ↑"
    
    if HAS_TK:
        out_file = filedialog.asksaveasfilename(
            title="Сохранить блокнот", initialdir=base_dir,
            initialfile="notebook.ipynb", filetypes=[("Jupyter Notebook", "*.ipynb")]
        )
    else:
        out_file = input("Укажите путь для сохранения (.ipynb): ").strip()
        
    if not out_file:
        sys.exit("Файл сохранения не выбран. Выход.")
        
    out_path = Path(out_file).resolve()
    script_path = Path(sys.argv[0]).resolve()
    skip_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", ".idea"}
    
    # Структура Jupyter-блокнота
    nb = {
        "cells": [], "nbformat": 4, "nbformat_minor": 4,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"}
        }
    }
    
    # Рекурсивный поиск файлов
    py_files = []
    for r, d, f in os.walk(base_dir):
        d[:] = [sub for sub in d if sub not in skip_dirs]
        for file in f:
            if file.endswith(".py"):
                py_files.append(Path(r) / file)
                
    # Исключаем сам скрипт и выходной файл
    py_files = [p for p in py_files if p not in (out_path, script_path)]
    
    # Сортировка файлов
    def sort_key(p):
        st = p.stat()
        rel = p.relative_to(base_dir)
        if crit == '2': val = st.st_mtime
        elif crit == '3': val = getattr(st, 'st_birthtime', st.st_ctime)
        elif crit == '4': val = st.st_size
        else: return rel
        # При убывании инвертируем числовой ключ
        return (-val if is_desc else val, rel)
        
    py_files.sort(key=sort_key, reverse=(is_desc if crit == '1' else False))
    
    added, skipped = 0, 0
    for p in py_files:
        rel_path = p.relative_to(base_dir).as_posix()
        content = None
        
        # Чтение с подбором кодировки
        for enc in ('utf-8-sig', 'cp1251'):
            try:
                content = p.read_text(encoding=enc)
                break
            except UnicodeDecodeError:
                pass
        
        if content is None:
            print(f"Ошибка чтения, пропущен: {rel_path}")
            skipped += 1
            continue
            
        # Форматирование даты изменения для заголовка
        dt_str = datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            
        nb["cells"].append({
            "cell_type": "markdown", "metadata": {}, 
            "source": [f"## {rel_path} (изменён: {dt_str})"]
        })
        nb["cells"].append({
            "cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": content.splitlines(keepends=True)
        })
        added += 1

    # Сохранение блокнота
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        
    print(f"\nГотово! Добавлено файлов: {added}, пропущено: {skipped}")
    print(f"Сортировка: {crit_names[crit]} ({dir_name})")
    print(f"Блокнот сохранён по пути: {out_path}")

if __name__ == "__main__":
    main()