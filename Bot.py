import asyncio
import logging
import openai
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web
from database import init_db, save_message, get_user_history, get_all_users, is_user_exists

# ============================================
# 2. НАСТРОЙКА
# ============================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5089723992  # ← ВАШ ID

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
client = openai.OpenAI(
    base_url="https://api.proxyapi.ru/v1",
)

user_history = {}

# ============================================
# 4. ЗАГРУЗКА БАЗЫ ЗНАНИЙ
# ============================================
print("📚 Загрузка базы знаний...")
KNOWLEDGE_PATH = "knowledge"
knowledge_base = ""

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
    print("⚠️ Папка 'knowledge' не найдена.")

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
# 6. СИСТЕМНЫЙ ПРОМПТ (ОСТАВЛЯЕМ ВАШ)
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
КОГДА СРАЗУ ПЕРЕДАВАТЬ НА СЕРВИС:
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
- Любая ситуация, требующая физического вмешательства
- Клиент сам предлагает вызвать мастера

ФОРМУЛИРОВКА: "По этой ситуации лучше обратиться в наш сервисный отдел. Напишите нам @OrlaufService или позвоните по номеру +79990635140. Специалист поможет с ремонтом или заменой."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
КОГДА ОТВЕЧАТЬ САМОМУ:
- Смазка полотна
- Натяжение ремня
- Чистка от пыли
- Расшифровка стандартных ошибок (OIL, E03 и т.д.)
- Сброс ошибки
- Регулировка сиденья, руля
- Замена батареек в пульсометре
- Профилактика и уход

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ТЕМЫ ВНЕ ТВОЕЙ КОМПЕТЕНЦИИ:
Офисные кресла, игровые кресла, силовые тренажёры, обычные велосипеды.
На такие вопросы отвечай: "К сожалению, я помогаю только по беговым дорожкам, велотренажёрам, спин-байкам, эллиптическим и гребным тренажёрам, а также массажным креслам. По вашему вопросу лучше обратиться в общий сервисный центр по номеру +79990635140."
"""


# ============================================
# 7-8.5. ОБРАБОТЧИКИ КОМАНД
# ============================================
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Здравствуйте! Вы обратились в сервисный центр.\n\n"
        "Опишите, пожалуйста, вашу проблему — я помогу найти решение.\n\n"
        "Если нужна помощь мастера — просто напишите об этом."
    )


@dp.message(Command("clear"))
async def clear_history(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_history:
        user_history[user_id] = []
        await message.answer("🧹 История диалога очищена!")
    else:
        await message.answer("📭 У вас нет сохранённой истории.")


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
        text += f"• {first_name} (@{username or 'нет'})\n  ID: {user_id}\n  Последняя активность: {last_seen}\n\n"
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
# 9. ОСНОВНОЙ ОБРАБОТЧИК
# ============================================
@dp.message(F.text)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text
    username = message.from_user.username or "нет"
    first_name = message.from_user.first_name

    is_new_user = False
    try:
        user_exists = await is_user_exists(user_id)
        if not user_exists:
            is_new_user = True
    except Exception as e:
        print(f"⚠️ Ошибка проверки пользователя: {e}")

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    if is_new_user:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🔔 Новый пользователь!\n\n👤 Имя: {first_name}\n📱 Username: @{username}\n🆔 ID: {user_id}\n💬 Первое сообщение: {user_text}"
            )
        except Exception as e:
            print(f"⚠️ Ошибка уведомления админа: {e}")

    try:
        await save_message(user_id, username, first_name, "user", user_text)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения в БД: {e}")

    try:
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append({"role": "user", "content": user_text})
        if len(user_history[user_id]) > 10:
            user_history[user_id] = user_history[user_id][-10:]

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if knowledge_base:
            messages.append({"role": "system", "content": f"Вот информация из документации:\n\n{knowledge_base}"})
        messages.extend(user_history[user_id])

        response = client.chat.completions.create(
            model="deepseek/deepseek-v4.1-flash",
            messages=messages,
            timeout=30.0
        )

        if response.choices and response.choices[0].message.content:
            answer = response.choices[0].message.content
        else:
            answer = "Не смог найти ответ. Попробуйте переформулировать вопрос."

        user_history[user_id].append({"role": "assistant", "content": answer})

        try:
            await save_message(user_id, username, first_name, "assistant", answer)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения в БД: {e}")

        await message.answer(answer)

    except Exception as e:
        await message.answer("Ошибка при генерации ответа. Попробуйте позже.")
        print(f"🔴 ОШИБКА: {e}")


# ==========================================
# === ЗАПУСК (ИСПРАВЛЕНО) ===
# ==========================================
async def start_web_server():
    """Веб-сервер для Render, работает в одном цикле с ботом"""
    app = web.Application()
    app.router.add_get('/', lambda request: web.Response(text="Bot is alive!"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ Веб-сервер запущен на порту {port}")


async def main():
    await init_db()
    print("🤖 Бот запущен!")
    print("📚 База знаний готова к работе.")

    print("⏳ Начинаю слушать Telegram (Start polling)...")

    # Запускаем веб-сервер в фоне внутри того же event loop
    asyncio.create_task(start_web_server())

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())