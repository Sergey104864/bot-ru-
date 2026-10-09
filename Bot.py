import asyncio
import logging
import openai
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from database import init_db, save_message, get_user_history, get_all_users, is_user_exists

# ============================================
# 2. НАСТРОЙКА
# ============================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5089723992  # ← ВАШ ID от @userinfobot

# ===== ДИАГНОСТИКА =====
print("=" * 60)
print("🔍 ВСЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
for key in sorted(os.environ.keys()):
    value = os.environ[key]
    if "TOKEN" in key or "KEY" in key or "API" in key:
        if len(value) > 20:
            value = value[:10] + "..." + value[-5:]
    print(f"   {key} = {value}")
print("=" * 60)
# =========================

# --- НАСТРОЙКА OPENAI (через ProxyAPI) ---
# OpenAI SDK сам читает OPENAI_API_KEY из переменных окружения
client = openai.OpenAI(
    base_url="https://api.proxyapi.ru/v1",
)

# ============================================
# 3. ПАМЯТЬ БОТА
# ============================================
user_history = {}

# ============================================
# 4. ЗАГРУЗКА БАЗЫ ЗНАНИЙ (просто текст)
# ============================================
print("📚 Загрузка базы знаний...")

KNOWLEDGE_PATH = "knowledge"
knowledge_base = ""  # Весь текст одним куском

if os.path.exists(KNOWLEDGE_PATH):
    for file in os.listdir(KNOWLEDGE_PATH):
        file_path = os.path.join(KNOWLEDGE_PATH, file)
        try:
            if file.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    knowledge_base += f"\n\n=== {file} ===\n\n" + f.read()
                print(f"✅ Загружен TXT: {file}")
            else:
                print(f"⚠️ Пропускаем: {file}")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки {file}: {e}")
else:
    print("⚠️ Папка 'knowledge' не найдена. Бот будет работать без базы знаний.")

# Обрезаем базу знаний до 30000 символов (лимит контекста ИИ)
if len(knowledge_base) > 30000:
    knowledge_base = knowledge_base[:30000]

print(f"✅ База знаний готова ({len(knowledge_base)} символов)")

# ============================================
# 5. НАСТРОЙКА БОТА
# ============================================
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============================================
# 6. СИСТЕМНЫЙ ПРОМПТ
# ============================================


SYSTEM_PROMPT = """
Ты — консультант сервисного центра. Специализируешься на:
- Беговых дорожках
- Велотренажёрах
- Спин-байках
- Эллиптических тренажёрах
- Гребных тренажёрах
- Массажных креслах

Общайся как живой ассистент, кратко и по делу.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПРАВИЛА ОБЩЕНИЯ:

1. Говори о себе только в мужском роде: «я помогу», «я рад», «я готов», «я подскажу». Никогда не используй женский род.
2. Не используй эмодзи.
3. Отвечай коротко (3-5 предложений).
4. Если нужна пошаговая инструкция — нумерованным списком.
5. Обращайся на «вы».
6. Не выдумывай. Не знаешь — передай на сервис.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПРАВИЛО ПО ГАРАНТИИ:

При вопросе про гарантию — СНАЧАЛА определи категорию оборудования:
- Если клиент упомянул «велотренажёр», «вело», «спин-байк» — используй ТОЛЬКО блок «ГАРАНТИЯ НА ВЕЛОТРЕНАЖЁРЫ»
- Если клиент упомянул «беговая дорожка», «дорожка» — используй ТОЛЬКО блок «ГАРАНТИЯ НА БЕГОВЫЕ ДОРОЖКИ»
- Если клиент НЕ уточнил категорию — спроси: «Уточните, пожалуйста, на какое оборудование?»

НИКОГДА не давай гарантию на беговую дорожку, если клиент спросил про велотренажёр. И наоборот.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
КОГДА СРАЗУ ПЕРЕДАВАТЬ НА СЕРВИС (без попыток решить самому):

Если клиент описывает одну из этих ситуаций — НЕ пытайся решить проблему сам. Сразу предложи связаться с сервисным отделом:

- Затянул педали, не может открутить
- Сорвал резьбу, сломал крепление
- Разобрал узел и не может собрать
- Повредил провод, кабель, шлейф
- Уронил, ударил оборудование
- Залил жидкостью
- Появился запах гари, дым, искры
- Сломал пластик, кожух, декоративную накладку
- Треснула рама или дека
- Сломалась рукоятка, педаль, сиденье
- Не работает пульт, дисплей, электроника
- Ошибка, которой нет в базе знаний
- Любая ситуация, требующая физического вмешательства или замены деталей
- Клиент сам предлагает вызвать мастера

ФОРМУЛИРОВКА ОТВЕТА В ЭТИХ СЛУЧАЯХ:

"По этой ситуации лучше обратиться в наш сервисный отдел. Напишите нам @OrlaufService или позвоните по номеру +79990635140. Специалист поможет с ремонтом или заменой."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
КОГДА ОТВЕЧАТЬ САМОМУ (без передачи):

Только для простых случаев, которые можно решить самостоятельно:
- Смазка полотна
- Натяжение ремня
- Чистка от пыли
- Расшифровка стандартных ошибок (OIL, E03 и т.д.)
- Сброс ошибки
- Регулировка сиденья, руля
- Замена батареек в пульсометре
- Профилактика и уход

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПРИМЕРЫ:

Клиент: "Затянул педали, не могу открутить"
Ответ: "По этой ситуации лучше обратиться в наш сервисный отдел. Напишите нам в Telegram или позвоните по номеру +79990635140. Специалист поможет."

Клиент: "Сломалась рукоятка"
Ответ: "По этой ситуации лучше обратиться в наш сервисный отдел. Напишите нам в Telegram или позвоните по номеру +79990635140. Специалист поможет с заменой."

Клиент: "Как смазать дорожку?"
Ответ: (даёшь инструкцию по смазке из базы знаний)

Клиент: "Что значит ошибка OIL?"
Ответ: (расшифровываешь ошибку из базы знаний)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ТЕМЫ ВНЕ ТВОЕЙ КОМПЕТЕНЦИИ:

Офисные кресла, игровые кресла, силовые тренажёры, обычные велосипеды.

На такие вопросы отвечай: "К сожалению, я помогаю только по беговым дорожкам, велотренажёрам, спин-байкам, эллиптическим и гребным тренажёрам, а также массажным креслам. По вашему вопросу лучше обратиться в общий сервисный центр по номеру +79990635140."
"""

# ============================================
# 7. ОБРАБОТЧИК /start
# ============================================


@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Здравствуйте! Вы обратились в сервисный центр.\n\n"
        "Опишите, пожалуйста, вашу проблему — я помогу найти решение.\n\n"
        "Если нужна помощь мастера — просто напишите об этом."
    )

# ============================================
# 8. ОБРАБОТЧИК /clear
# ============================================
@dp.message(Command("clear"))
async def clear_history(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_history:
        user_history[user_id] = []
        await message.answer("🧹 История диалога очищена!")
    else:
        await message.answer("📭 У вас нет сохранённой истории.")


# ============================================
# 8.5. АДМИН-КОМАНДЫ
# ============================================

@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда только для администратора.")
        return

    users = await get_all_users()
    if not users:
        await message.answer("Пока нет пользователей.")
        return

    text = "👥 Пользователи:\n\n"
    for user_id, username, first_name, last_seen in users:
        text += f"• {first_name} (@{username or 'нет'})\n"
        text += f"  ID: {user_id}\n"
        text += f"  Последняя активность: {last_seen}\n\n"

    await message.answer(text[:4000])


@dp.message(Command("dialog"))
async def cmd_dialog(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда только для администратора.")
        return

    try:
        parts = message.text.split()
        user_id = int(parts[1])
    except (IndexError, ValueError):
        await message.answer("Использование: /dialog <user_id>\nНапример: /dialog 5089723992")
        return

    history = await get_user_history(user_id)
    if not history:
        await message.answer("История для этого пользователя пуста.")
        return

    text = f"💬 Диалог с пользователем {user_id}:\n\n"
    for role, content, timestamp in history:
        prefix = "👤" if role == "user" else "🤖"
        text += f"{prefix} {content}\n\n"

    await message.answer(text[:4000])




# ============================================
# 9. ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ
# ============================================
@dp.message(F.text)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text
    username = message.from_user.username or "нет"
    first_name = message.from_user.first_name

    # === ПРОВЕРЯЕМ, НОВЫЙ ЛИ ПОЛЬЗОВАТЕЛЬ ===
    is_new_user = False
    try:
        user_exists = await is_user_exists(user_id)
        if not user_exists:
            is_new_user = True
    except Exception as e:
        print(f"⚠️ Ошибка проверки пользователя: {e}")

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # === УВЕДОМЛЕНИЕ АДМИНУ О НОВОМ ПОЛЬЗОВАТЕЛЕ ===
    if is_new_user:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🔔 Новый пользователь!\n\n"
                f"👤 Имя: {first_name}\n"
                f"📱 Username: @{username}\n"
                f"🆔 ID: {user_id}\n"
                f"💬 Первое сообщение: {user_text}"
            )
        except Exception as e:
            print(f"⚠️ Ошибка уведомления админа: {e}")

    # === СОХРАНЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ В БД ===
    try:
        await save_message(user_id, username, first_name, "user", user_text)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения в БД: {e}")

    try:
        # --- РАБОТА С ПАМЯТЬЮ ---
        if user_id not in user_history:
            user_history[user_id] = []

        user_history[user_id].append({"role": "user", "content": user_text})

        if len(user_history[user_id]) > 10:
            user_history[user_id] = user_history[user_id][-10:]

        # --- ФОРМИРУЕМ ЗАПРОС К ИИ ---
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        if knowledge_base:
            messages.append({
                "role": "system",
                "content": f"Вот информация из документации:\n\n{knowledge_base}"
            })

        messages.extend(user_history[user_id])

        # --- ОТПРАВКА ЗАПРОСА В PROXYAPI ---
        response = client.chat.completions.create(
            model="deepseek/deepseek-v4.1-flash",
            messages=messages,
            timeout=30.0
        )

        # --- БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ОТВЕТА ---
        if response.choices and response.choices[0].message.content:
            answer = response.choices[0].message.content
        else:
            answer = "Не смог найти ответ. Попробуйте переформулировать вопрос."

        user_history[user_id].append({"role": "assistant", "content": answer})

        # === СОХРАНЯЕМ ОТВЕТ БОТА В БД ===
        try:
            await save_message(user_id, username, first_name, "assistant", answer)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения в БД: {e}")

        await message.answer(answer)

    except Exception as e:
        await message.answer("Ошибка при генерации ответа. Попробуйте позже.")
        print(f"🔴 ОШИБКА: {e}")


# ==========================================
# === ВЕБ-СЕРВЕР ДЛЯ RENDER ===
# ==========================================
import threading
from aiohttp import web


def run_web_server():
    """Веб-сервер в отдельном потоке"""

    async def handle(request):
        return web.Response(text="Bot is alive!")

    async def web_server():
        app = web.Application()
        app.router.add_get('/', handle)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get('PORT', 8080))
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"✅ Веб-сервер запущен на порту {port}")
        await asyncio.Event().wait()

    asyncio.run(web_server())


# ==========================================
# === ЗАПУСК ===
# ==========================================

async def main():
    # ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
    await init_db()

    print("🤖 Бот запущен!")
    print("📚 База знаний готова к работе.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    asyncio.run(main())




"""
database.py — модуль для работы с базой данных бота.
"""

import aiosqlite
from datetime import datetime


DB_PATH = "bot_history.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    print("✅ База данных готова")


async def save_message(user_id: int, username: str, first_name: str, role: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (user_id, username, first_name, role, content) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, first_name, role, content)
        )
        await db.commit()


async def get_user_history(user_id: int, limit: int = 20):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT role, content, timestamp FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return rows[::-1]


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT DISTINCT user_id, username, first_name, MAX(timestamp) as last_seen 
            FROM messages 
            GROUP BY user_id 
            ORDER BY last_seen DESC
        """)
        rows = await cursor.fetchall()
        return rows


async def is_user_exists(user_id: int) -> bool:
    """Проверяет, есть ли пользователь в базе данных."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM messages WHERE user_id = ? LIMIT 1",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row is not None