import asyncio
import logging
import openai
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from dotenv import load_dotenv




# ============================================
# 1. НАСТРОЙКИ
# ============================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

# ============================================
# 2. НАСТРОЙКА OPENROUTER
# ============================================
client = openai.OpenAI(
    api_key=OPENROUTER_KEY,
    base_url="https://openrouter.ai/api/v1",
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

ПРАВИЛА:
1. Не используй эмодзи.
2. Отвечай коротко (3-5 предложений).
3. Если нужна пошаговая инструкция — нумерованным списком.
4. Если проблема серьёзная — предложи вызвать мастера.
5. Если не знаешь — скажи честно.
6. Обращайся на «вы».


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПРАВИЛА ОБЩЕНИЯ:

1. Представляйся только при первом сообщении в сутки. При последующих — сразу по делу.
2. Отвечай коротко. Максимум 3-5 предложений, если не нужна пошаговая инструкция.
3. Не используй эмодзи.
4. Не используй символы ✅, ⚠️, 🔧, ❗ и капс в заголовках.
5. Пошаговые инструкции — нумерованным списком.
6. Обращайся на «вы», вежливо, но без официоза.
7. Не выдумывай. Не знаешь — скажи честно.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ТИПОВЫЕ ТЕМЫ:

- Беговые дорожки: перегрев, проскальзывание, ошибка OIL, бьёт током, смазка, натяжение
- Велотренажёры: нет нагрузки, шум, скрип, педали, сиденье
- Спин-байки: нет нагрузки, шум, скрип, регулировка сиденья
- Эллиптические: скрип, шатание, педали, рукоятки
- Гребные: скрип, ремень, сиденье, датчики
- Массажные кресла: не включается, застряло, слабый массаж, пульт

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ТЕМЫ ВНЕ ТВОЕЙ КОМПЕТЕНЦИИ:

Офисные кресла, игровые кресла, силовые тренажёры, обычные велосипеды, всё остальное.

На такие вопросы отвечай: «К сожалению, я помогаю только по беговым дорожкам, велотренажёрам, спин-байкам, эллиптическим и гребным тренажёрам, а также массажным креслам. По вашему вопросу лучше обратиться в общий сервисный центр.»
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
# 9. ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ
# ============================================
@dp.message(F.text)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

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

        # Добавляем базу знаний (если она есть)
        if knowledge_base:
            messages.append({
                "role": "system",
                "content": f"Вот информация из документации:\n\n{knowledge_base}"
            })

        messages.extend(user_history[user_id])

        # --- ОТПРАВКА ЗАПРОСА В OPENROUTER ---
        response = client.chat.completions.create(
            model="inclusionai/ling-3.0-flash-fin:free",
            messages=messages,
            timeout=30.0,
            extra_headers={
                "HTTP-Referer": "https://localhost",
                "X-Title": "Service Bot"
            }
        )

        # --- БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ОТВЕТА ---
        if response.choices and response.choices[0].message.content:
            answer = response.choices[0].message.content
        else:
            answer = "🤔 Я не смог найти ответ. Попробуйте переформулировать вопрос."

        user_history[user_id].append({"role": "assistant", "content": answer})

        await message.answer(answer)

    except Exception as e:
        await message.answer("⚠️ Ошибка при генерации ответа. Попробуйте позже.")
        print(f"🔴 ОШИБКА: {e}")

# ============================================
# 10. ЗАПУСК
# ============================================
async def main():
    print("🤖 Бот запущен!")
    print("📚 База знаний готова к работе.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())