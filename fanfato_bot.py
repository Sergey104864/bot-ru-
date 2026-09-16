import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ============================================
# 1. ТОКЕН (ВСТАВЬ СВОЙ!)
# ============================================
BOT_TOKEN = "8636349611:AAFbTt9wsjQh2hTZDQcJ0kyWREgpPLCU59A"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============================================
# 2. БАЗА ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ (ВРЕМЕННАЯ)
# ============================================
user_data = {}


def get_user_data(user_id: int) -> dict:
    """Безопасно получает данные пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {}
    return user_data[user_id]


# ============================================
# 3. БАЗА ДАННЫХ САПБОРДОВ
# ============================================

BOARDS = {
    "surfer": {
        "name": "🏄 Fanfato SUP Surfer",
        "size": "10'6\" x 32\" x 6\"",
        "volume": "220 л",
        "weight": "9.5 кг",
        "load": "до 120 кг",
        "best_for": "Озёра, спокойная вода, прогулки",
        "price": "45 000 ₽",
        "description": "Идеальный выбор для начинающих и любителей спокойных прогулок. Устойчив и надёжен."
    },
    "pro": {
        "name": "🔥 Fanfato SUP Pro",
        "size": "12'6\" x 28\" x 6\"",
        "volume": "280 л",
        "weight": "10.2 кг",
        "load": "до 140 кг",
        "best_for": "Спорт, гонки, большие расстояния",
        "price": "65 000 ₽",
        "description": "Профессиональная модель для спортивных гонок и длительных заплывов. Максимальная скорость."
    },
    "tour": {
        "name": "🌊 Fanfato SUP Tour",
        "size": "11'6\" x 32\" x 6\"",
        "volume": "250 л",
        "weight": "9.8 кг",
        "load": "до 130 кг",
        "best_for": "Туризм, походы, реки",
        "price": "52 000 ₽",
        "description": "Универсальная модель для туризма и походов. Отлично держит курс."
    },
    "inflatable": {
        "name": "🎈 Fanfato SUP Inflatable",
        "size": "10' x 33\" x 6\"",
        "volume": "200 л",
        "weight": "8.5 кг",
        "load": "до 110 кг",
        "best_for": "Хранение в квартире, путешествия, новички",
        "price": "38 000 ₽",
        "description": "Надувная модель, которая помещается в рюкзак. Идеально для городских жителей."
    }
}


# ============================================
# 4. КОМАНДА /start
# ============================================

@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏄 Подобрать сапборд", callback_data="select_board")],
            [InlineKeyboardButton(text="❓ Частые вопросы", callback_data="faq")],
            [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="order")],
            [InlineKeyboardButton(text="📦 Статус доставки", callback_data="delivery")],
        ]
    )

    await message.answer(
        f"🌊 <b>Fanfato SUP — гид по выбору сапборда!</b>\n\n"
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я — ваш персональный помощник по подбору сапбордов.\n"
        "Помогу вам выбрать идеальную модель, отвечу на вопросы и оформлю заказ.\n\n"
        "📌 <b>Что я умею:</b>\n"
        "🏄 Подобрать сапборд по вашим параметрам\n"
        "❓ Ответить на частые вопросы\n"
        "🛒 Помочь с оформлением заказа\n"
        "📦 Отследить статус доставки\n\n"
        "Начните с кнопки «Подобрать сапборд» или просто напишите вопрос.\n\n"
        "📞 Контакт: +7 999 123-45-67\n"
        "🌐 Сайт: fanfato-sup.ru\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ============================================
# 5. ПОДБОР САПБОРДА (опрос)
# ============================================

@dp.callback_query(F.data == "select_board")
async def select_board(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    get_user_data(user_id)  # Создаём запись для пользователя, если её нет

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📍 Озеро / спокойная вода", callback_data="water_lake")],
            [InlineKeyboardButton(text="🌊 Река / течение", callback_data="water_river")],
            [InlineKeyboardButton(text="🏄 Море / волны", callback_data="water_sea")],
            [InlineKeyboardButton(text="🎯 Не знаю, я новичок", callback_data="water_newbie")],
        ]
    )

    await callback.message.edit_text(
        "🏄 <b>Где вы планируете кататься?</b>\n\n"
        "Выберите вариант:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("water_"))
async def get_water(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)

    water_map = {
        "water_lake": "Озеро / спокойная вода",
        "water_river": "Река / течение",
        "water_sea": "Море / волны",
        "water_newbie": "Новичок (не знаю)"
    }
    data["water"] = water_map.get(callback.data, "Не указано")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬆️ До 70 кг", callback_data="weight_light")],
            [InlineKeyboardButton(text="⬆️ 70-90 кг", callback_data="weight_mid")],
            [InlineKeyboardButton(text="⬆️ 90-110 кг", callback_data="weight_heavy")],
            [InlineKeyboardButton(text="⬆️ Более 110 кг", callback_data="weight_plus")],
        ]
    )

    await callback.message.edit_text(
        "⚖️ <b>Какой у вас вес?</b>\n\n"
        "Выберите диапазон:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("weight_"))
async def get_weight(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)

    weight_map = {
        "weight_light": "До 70 кг",
        "weight_mid": "70-90 кг",
        "weight_heavy": "90-110 кг",
        "weight_plus": "Более 110 кг"
    }
    data["weight"] = weight_map.get(callback.data, "Не указано")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌿 Новичок", callback_data="level_newbie")],
            [InlineKeyboardButton(text="🏄 Любитель", callback_data="level_mid")],
            [InlineKeyboardButton(text="🔥 Профи", callback_data="level_pro")],
        ]
    )

    await callback.message.edit_text(
        "🎯 <b>Ваш уровень подготовки?</b>\n\n"
        "Выберите вариант:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("level_"))
async def get_level(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)

    level_map = {
        "level_newbie": "Новичок",
        "level_mid": "Любитель",
        "level_pro": "Профи"
    }
    data["level"] = level_map.get(callback.data, "Не указано")

    await show_recommendation(callback)


async def show_recommendation(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_data(user_id)

    # Логика подбора
    recommendation = "surfer"  # по умолчанию

    if data.get("weight") == "Более 110 кг" or data.get("water") == "Море / волны":
        recommendation = "pro"
    elif data.get("water") == "Река / течение" or data.get("level") == "Профи":
        recommendation = "tour"
    elif data.get("level") == "Новичок" and data.get("water") == "Озеро / спокойная вода":
        recommendation = "inflatable"
    elif data.get("weight") == "До 70 кг":
        recommendation = "inflatable"
    elif data.get("water") == "Озеро / спокойная вода":
        recommendation = "surfer"
    elif data.get("water") == "Новичок (не знаю)":
        recommendation = "surfer"

    board = BOARDS[recommendation]

    text = (
        f"🏄 <b>Мы подобрали для вас!</b>\n\n"
        f"<b>{board['name']}</b>\n"
        f"📏 Размер: {board['size']}\n"
        f"📦 Объём: {board['volume']}\n"
        f"⚖️ Вес доски: {board['weight']}\n"
        f"🏋️ Макс. нагрузка: {board['load']}\n"
        f"📍 Лучшее применение: {board['best_for']}\n"
        f"💰 Цена: {board['price']}\n\n"
        f"📝 {board['description']}\n\n"
        f"<i>Подобрано на основе ваших ответов:</i>\n"
        f"🌊 Вода: {data.get('water')}\n"
        f"⚖️ Вес: {data.get('weight')}\n"
        f"🎯 Уровень: {data.get('level')}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Оформить заказ", callback_data="order")],
            [InlineKeyboardButton(text="🔄 Подобрать заново", callback_data="select_board")],
            [InlineKeyboardButton(text="📋 Главное меню", callback_data="menu")],
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================
# 6. FAQ (Частые вопросы)
# ============================================

@dp.callback_query(F.data == "faq")
async def show_faq(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Из чего сделан сапборд?", callback_data="faq_material")],
            [InlineKeyboardButton(text="💨 Какой насос нужен?", callback_data="faq_pump")],
            [InlineKeyboardButton(text="🚚 Сколько стоит доставка?", callback_data="faq_delivery")],
            [InlineKeyboardButton(text="🔧 Как ухаживать за сапбордом?", callback_data="faq_care")],
            [InlineKeyboardButton(text="🔄 Назад", callback_data="menu")],
        ]
    )

    await callback.message.edit_text(
        "❓ <b>Частые вопросы</b>\n\n"
        "Выберите вопрос:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("faq_"))
async def faq_answer(callback: types.CallbackQuery):
    answers = {
        "faq_material": "📦 <b>Из чего сделан сапборд?</b>\n\nСапборды Fanfato SUP сделаны из высококачественного ПВХ с дроп-стич технологией. Это обеспечивает прочность и жёсткость как у жесткой доски.",
        "faq_pump": "💨 <b>Какой насос нужен?</b>\n\nВ комплекте с сапбордом идёт ручной насос. Рекомендуем использовать его. Для быстрой накачки можно приобрести электрический насос (опция).",
        "faq_delivery": "🚚 <b>Сколько стоит доставка?</b>\n\nДоставка по городу — бесплатно. По области — от 500 ₽. Срок доставки: 1-3 дня.",
        "faq_care": "🔧 <b>Как ухаживать за сапбордом?</b>\n\n1. Мойте пресной водой после солёной\n2. Храните в сухом месте\n3. Избегайте прямых солнечных лучей\n4. Спускайте воздух при длительном хранении"
    }

    answer = answers.get(callback.data, "Информация временно недоступна.")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к вопросам", callback_data="faq")],
            [InlineKeyboardButton(text="📋 Главное меню", callback_data="menu")],
        ]
    )

    await callback.message.edit_text(
        answer,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================
# 7. ЗАЯВКА
# ============================================

@dp.callback_query(F.data == "order")
async def start_order(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="order_form")],
            [InlineKeyboardButton(text="📋 Главное меню", callback_data="menu")],
        ]
    )

    await callback.message.edit_text(
        "🛒 <b>Оформление заказа</b>\n\n"
        "Напишите в следующем сообщении:\n"
        "1. Ваше имя\n"
        "2. Номер телефона\n"
        "3. Модель сапборда\n"
        "4. Адрес доставки\n\n"
        "Например:\n"
        "Иван, +7 999 123-45-67, Surfer, ул. Ленина 1",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "order_form")
async def order_form(callback: types.CallbackQuery):
    await callback.message.answer(
        "📝 <b>Заполните заявку</b>\n\n"
        "Напишите:\n"
        "• Ваше имя\n"
        "• Телефон\n"
        "• Модель сапборда\n"
        "• Адрес\n\n"
        "<i>Например: Иван, +7 999 123-45-67, Surfer, ул. Ленина 1</i>",
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================
# 8. СТАТУС ДОСТАВКИ
# ============================================

@dp.callback_query(F.data == "delivery")
async def delivery_status(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Главное меню", callback_data="menu")],
        ]
    )

    await callback.message.edit_text(
        "📦 <b>Статус доставки</b>\n\n"
        "Чтобы узнать статус заказа, отправьте номер заказа.\n\n"
        "Пример: <code>#12345</code>\n\n"
        "Мы пришлём актуальную информацию.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================
# 9. ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ
# ============================================

@dp.message()
async def handle_text(message: types.Message):
    text = message.text.lower()

    if "заказ" in text or "номер" in text and "#" in text:
        await message.answer(
            "📦 <b>Статус заказа</b>\n\n"
            f"Заказ {text} — в пути. Ожидайте доставку через 2-3 дня.\n\n"
            "📞 По вопросам: +7 999 123-45-67",
            parse_mode="HTML"
        )
    elif "заявка" in text or "имя" in text and "+" in text:
        await message.answer(
            "✅ <b>Заявка принята!</b>\n\n"
            "Спасибо! Наш менеджер свяжется с вами в течение 15 минут.\n\n"
            "📋 Главное меню: /start",
            parse_mode="HTML"
        )
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏄 Подобрать сапборд", callback_data="select_board")],
                [InlineKeyboardButton(text="❓ Частые вопросы", callback_data="faq")],
                [InlineKeyboardButton(text="📋 Главное меню", callback_data="menu")],
            ]
        )
        await message.answer(
            "🤔 Я не совсем понял. Попробуйте выбрать действие:",
            reply_markup=keyboard
        )


# ============================================
# 10. ВОЗВРАТ В ГЛАВНОЕ МЕНЮ
# ============================================

@dp.callback_query(F.data == "menu")
async def back_to_menu(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏄 Подобрать сапборд", callback_data="select_board")],
            [InlineKeyboardButton(text="❓ Частые вопросы", callback_data="faq")],
            [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="order")],
            [InlineKeyboardButton(text="📦 Статус доставки", callback_data="delivery")],
        ]
    )

    await callback.message.edit_text(
        "🌊 <b>Fanfato SUP — гид по выбору сапборда!</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================
# 11. ЗАПУСК
# ============================================

async def main():
    print("🤖 Бот Fanfato SUP запущен!")
    print("🏄 Готов помогать с выбором сапбордов!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())