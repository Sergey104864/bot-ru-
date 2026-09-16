import os
import sys
from pathlib import Path

# ============================================
# БАЗА ЗНАНИЙ (все данные здесь)
# ============================================

KNOWLEDGE_BASE = {}


def load_pdf(file_path: str) -> str:
    """Читает PDF файл и возвращает текст"""
    try:
        # Пытаемся импортировать PyPDF2
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except ImportError:
        print("⚠️ PyPDF2 не установлен. Установите: pip install PyPDF2")
        return ""
    except Exception as e:
        print(f"❌ Ошибка чтения PDF: {e}")
        return ""


def load_all_files(folder_path: str):
    """Загружает все файлы из папки"""
    folder = Path(folder_path)

    if not folder.exists():
        print(f"❌ Папка '{folder_path}' не найдена!")
        return

    print(f"📂 Сканирую папку: {folder_path}")
    print("=" * 50)

    files_found = list(folder.iterdir())
    pdf_files = [f for f in files_found if f.suffix.lower() == '.pdf']

    if not pdf_files:
        print("📄 PDF файлы не найдены!")
        return

    print(f"📄 Найдено PDF файлов: {len(pdf_files)}")
    print("=" * 50)

    for file_path in pdf_files:
        print(f"📖 Читаю: {file_path.name}")

        # Читаем PDF
        content = load_pdf(str(file_path))

        if content:
            # Сохраняем в базу знаний
            key = file_path.stem  # Имя файла без расширения
            KNOWLEDGE_BASE[key] = {
                "name": file_path.name,
                "content": content,
                "path": str(file_path)
            }
            print(f"   ✅ Добавлено: {file_path.name} ({len(content)} символов)")
        else:
            print(f"   ⚠️ Не удалось прочитать: {file_path.name}")

    print("=" * 50)
    print(f"✅ Загружено файлов: {len(KNOWLEDGE_BASE)}")
    print(f"📚 Всего символов: {sum(len(v['content']) for v in KNOWLEDGE_BASE.values())}")


def search_knowledge(query: str) -> str:
    """Ищет информацию в базе знаний"""
    query_lower = query.lower()
    results = []

    for key, data in KNOWLEDGE_BASE.items():
        content = data["content"].lower()
        if query_lower in content:
            # Находим кусок текста с запросом
            text = data["content"]
            results.append(f"📄 {data['name']}:\n{text[:500]}...\n")

    if results:
        return "\n".join(results)
    else:
        return "❌ Ничего не найдено по вашему запросу."


if __name__ == "__main__":
    # Путь к папке
    folder_path = sys.argv[1] if len(sys.argv) > 1 else "./knowledge"

    # Загружаем файлы
    load_all_files(folder_path)

    # Тестируем поиск
    print("\n🔍 Проверка поиска:")
    print("=" * 50)
    test_query = input("Введите запрос для поиска (или Enter для выхода): ")
    if test_query:
        result = search_knowledge(test_query)
        print(result)