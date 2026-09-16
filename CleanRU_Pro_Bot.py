import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ============================================
# 1. НАСТРОЙКИ
# ============================================
BOT_TOKEN = "8917343780:AAFzlz3R-4nr5OUD3MaZft9o_56SgzOTCfg"
ADMIN_ID = 5089723992              # Ваш ID от @userinfobot

# ============================================
# 2. НАСТРОЙКА БОТА
# ============================================
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ============================================
# 3. ВРЕМЕННОЕ ХРАНИЛИЩЕ (ДЛЯ ЗАЯВОК)
# ============================================
user_orders = {}


def get_user_order(user_id: int) -> dict:
    """Безопасно получает данные заявки пользователя"""
    if user_id not in user_orders:
        user_orders[user_id] = {}
    return user_orders[user_id]


# ============================================
# 4. СОСТОЯНИЯ ДЛЯ ЗАЯВКИ (FSM)
# ============================================
class OrderStates(StatesGroup):
    name = State()
    phone = State()
    address = State()
    cleaning_type = State()
    area = State()
    date = State()
    confirm = State()


# ============================================
# 5. КОМАНДА /start
# ============================================
@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧮 Рассчитать стоимость", callback_data="calc")],
            [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="order")],
            [InlineKeyboardButton(text="❓ Частые вопросы", callback_data="faq")],
            [InlineKeyboardButton(text="📞 Связаться с нами", callback_data="contacts")],
        ]
    )

    await message.answer(
        f"<b>CleanRU - Ваш помощник по уборке</b>\n\n"
        f" Здравствуйте, {message.from_user.first_name}!\n\n"
        "Я помогу вам:\n"
        "🧮 Рассчитать стоимость уборки\n"
        "📝 Оставить заявку\n"
        "❓ Ответить на частые вопросы\n"
        "📞 Связаться с нашей командой\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ============================================
# 6. FAQ — ЧАСТЫЕ ВОПРОСЫ
# ============================================
@dp.callback_query(F.data == "faq")
async def show_faq(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Сколько стоит уборка?", callback_data="faq_price")],
            [InlineKeyboardButton(text="⏱️ Сколько времени занимает?", callback_data="faq_time")],
            [InlineKeyboardButton(text="🧴 Что входит в уборку?", callback_data="faq_include")],
            [InlineKeyboardButton(text="👷 Кто будет убирать?", callback_data="faq_staff")],
            [InlineKeyboardButton(text="🔄 Можно ли перенести?", callback_data="faq_reschedule")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu")],
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
        "faq_price": (
            "💰 <b>Сколько стоит уборка?</b>\n\n"
            "Стоимость зависит от:\n"
            "• Площади помещения\n"
            "• Типа уборки (поддерживающая, генеральная, после ремонта)\n"
            "• Дополнительных услуг\n\n"
            "Примерные цены:\n"
            "• Поддерживающая: от 50 ₽/м²\n"
            "• Генеральная: от 80 ₽/м²\n"
            "• После ремонта: от 120 ₽/м²\n\n"
            "🧮 Точную стоимость можно рассчитать в калькуляторе."
        ),
        "faq_time": (
            "⏱️ <b>Сколько времени занимает уборка?</b>\n\n"
            "Стандартная уборка квартиры 50 м² занимает 2-3 часа.\n"
            "Генеральная уборка — 4-6 часов.\n"
            "После ремонта — 5-8 часов.\n\n"
            "Точное время зависит от степени загрязнения."
        ),
        "faq_include": (
            "🧴 <b>Что входит в уборку?</b>\n\n"
            "✅ Влажная уборка полов\n"
            "✅ Протирание пыли\n"
            "✅ Мытьё окон (по желанию)\n"
            "✅ Уборка кухни\n"
            "✅ Уборка санузлов\n"
            "✅ Вынос мусора\n\n"
            "Всё оборудование и моющие средства мы привозим сами."
        ),
        "faq_staff": (
            "👷 <b>Кто будет убирать?</b>\n\n"
            "Наши сотрудники:\n"
            "• Прошли обучение\n"
            "• Имеют опыт работы\n"
            "• Работают с профессиональной химией\n"
            "• Застрахованы\n\n"
            "Вы можете выбрать одного клинера или команду."
        ),
        "faq_reschedule": (
            "🔄 <b>Можно ли перенести уборку?</b>\n\n"
            "Да, перенести можно бесплатно не позднее чем за 24 часа до начала.\n"
            "Свяжитесь с нами по телефону или в Telegram."
        ),
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
# 7. КАЛЬКУЛЯТОР СТОИМОСТИ
# ============================================
@dp.callback_query(F.data == "calc")
async def calc_start(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Квартира", callback_data="calc_type_flat")],
            [InlineKeyboardButton(text="🏢 Офис", callback_data="calc_type_office")],
            [InlineKeyboardButton(text="🏡 Дом", callback_data="calc_type_house")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu")],
        ]
    )

    await callback.message.edit_text(
        "🧮 <b>Калькулятор стоимости</b>\n\n"
        "Выберите тип помещения:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("calc_type_"))
async def calc_area(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    order = get_user_order(user_id)

    type_map = {
        "calc_type_flat": "Квартира",
        "calc_type_office": "Офис",
        "calc_type_house": "Дом"
    }
    order["type"] = type_map.get(callback.data, "Не указано")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="До 30 м²", callback_data="calc_area_30")],
            [InlineKeyboardButton(text="30-50 м²", callback_data="calc_area_50")],
            [InlineKeyboardButton(text="50-80 м²", callback_data="calc_area_80")],
            [InlineKeyboardButton(text="80-120 м²", callback_data="calc_area_120")],
            [InlineKeyboardButton(text="Более 120 м²", callback_data="calc_area_120plus")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="calc")],
        ]
    )

    await callback.message.edit_text(
        f"🏠 Тип: <b>{order['type']}</b>\n\n"
        "Выберите площадь помещения:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("calc_area_"))
async def calc_cleaning_type(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    order = get_user_order(user_id)

    area_map = {
        "calc_area_30": "До 30 м²",
        "calc_area_50": "30-50 м²",
        "calc_area_80": "50-80 м²",
        "calc_area_120": "80-120 м²",
        "calc_area_120plus": "Более 120 м²"
    }
    order["area"] = area_map.get(callback.data, "Не указано")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧹 Поддерживающая", callback_data="calc_clean_support")],
            [InlineKeyboardButton(text="✨ Генеральная", callback_data="calc_clean_general")],
            [InlineKeyboardButton(text="🔨 После ремонта", callback_data="calc_clean_repair")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="calc")],
        ]
    )

    await callback.message.edit_text(
        f"🏠 Тип: <b>{order['type']}</b>\n"
        f"📐 Площадь: <b>{order['area']}</b>\n\n"
        "Выберите тип уборки:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("calc_clean_"))
async def calc_result(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    order = get_user_order(user_id)

    clean_map = {
        "calc_clean_support": ("Поддерживающая", 50),
        "calc_clean_general": ("Генеральная", 80),
        "calc_clean_repair": ("После ремонта", 120)
    }
    clean_type, price_per_m2 = clean_map.get(callback.data, ("Не указано", 0))
    order["cleaning_type"] = clean_type

    # Расчёт стоимости
    area_prices = {
        "До 30 м²": 30,
        "30-50 м²": 40,
        "50-80 м²": 65,
        "80-120 м²": 100,
        "Более 120 м²": 120
    }
    area_m2 = area_prices.get(order["area"], 50)
    total_price = area_m2 * price_per_m2

    # Дополнительные услуги
    extra_price = 0
    if order["type"] == "Офис":
        extra_price = 500
    elif order["type"] == "Дом":
        extra_price = 1000

    final_price = total_price + extra_price

    # Сохраняем в заявку
    order["estimated_price"] = final_price

    text = (
        f"🧮 <b>Расчёт стоимости</b>\n\n"
        f"🏠 Тип: {order['type']}\n"
        f"📐 Площадь: {order['area']}\n"
        f"🧹 Тип уборки: {clean_type}\n\n"
        f"💰 <b>Примерная стоимость: {final_price} ₽</b>\n\n"
        f"<i>Точная цена может отличаться в зависимости от степени загрязнения.</i>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="order")],
            [InlineKeyboardButton(text="🔄 Пересчитать", callback_data="calc")],
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
# 8. ЗАЯВКА (FSM)
# ============================================
@dp.callback_query(F.data == "order")
async def order_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "📝 <b>Оформление заявки</b>\n\n"
        "👤 Как вас зовут?",
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.name)
    await callback.answer()


@dp.message(OrderStates.name)
async def order_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📞 Напишите ваш номер телефона:")
    await state.set_state(OrderStates.phone)


@dp.message(OrderStates.phone)
async def order_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("📍 Напишите адрес (город, улица, дом, квартира):")
    await state.set_state(OrderStates.address)


@dp.message(OrderStates.address)
async def order_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Квартира", callback_data="ord_type_flat")],
            [InlineKeyboardButton(text="🏢 Офис", callback_data="ord_type_office")],
            [InlineKeyboardButton(text="🏡 Дом", callback_data="ord_type_house")],
        ]
    )

    await message.answer(
        "🏠 Выберите тип помещения:",
        reply_markup=keyboard
    )
    await state.set_state(OrderStates.cleaning_type)


@dp.callback_query(F.data.startswith("ord_type_"), OrderStates.cleaning_type)
async def order_type(callback: types.CallbackQuery, state: FSMContext):
    type_map = {
        "ord_type_flat": "Квартира",
        "ord_type_office": "Офис",
        "ord_type_house": "Дом"
    }
    await state.update_data(room_type=type_map.get(callback.data, "Не указано"))

    await callback.message.edit_text(
        "📐 Напишите площадь помещения (в м²):\n"
        "Например: 45"
    )
    await state.set_state(OrderStates.area)
    await callback.answer()


@dp.message(OrderStates.area)
async def order_area(message: types.Message, state: FSMContext):
    await state.update_data(area=message.text)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧹 Поддерживающая", callback_data="ord_clean_support")],
            [InlineKeyboardButton(text="✨ Генеральная", callback_data="ord_clean_general")],
            [InlineKeyboardButton(text="🔨 После ремонта", callback_data="ord_clean_repair")],
        ]
    )

    await message.answer(
        "🧹 Выберите тип уборки:",
        reply_markup=keyboard
    )
    await state.set_state(OrderStates.cleaning_type)


@dp.callback_query(F.data.startswith("ord_clean_"), OrderStates.cleaning_type)
async def order_clean_type(callback: types.CallbackQuery, state: FSMContext):
    clean_map = {
        "ord_clean_support": "Поддерживающая",
        "ord_clean_general": "Генеральная",
        "ord_clean_repair": "После ремонта"
    }
    await state.update_data(cleaning_type=clean_map.get(callback.data, "Не указано"))

    await callback.message.edit_text(
        "📅 Напишите желаемую дату и время уборки:\n"
        "Например: 25.12.2024, 14:00"
    )
    await state.set_state(OrderStates.date)
    await callback.answer()


@dp.message(OrderStates.date)
async def order_date(message: types.Message, state: FSMContext):
    await state.update_data(date=message.text)

    data = await state.get_data()

    text = (
        f"📋 <b>Проверьте заявку:</b>\n\n"
        f"👤 Имя: {data.get('name')}\n"
        f"📞 Телефон: {data.get('phone')}\n"
        f"📍 Адрес: {data.get('address')}\n"
        f"🏠 Тип: {data.get('room_type')}\n"
        f"📐 Площадь: {data.get('area')} м²\n"
        f"🧹 Уборка: {data.get('cleaning_type')}\n"
        f"📅 Дата: {data.get('date')}\n\n"
        "Всё верно?"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="menu")],
        ]
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(OrderStates.confirm)


@dp.callback_query(F.data == "confirm_order", OrderStates.confirm)
async def order_confirm(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # Отправляем админу
    admin_text = (
        f"📩 <b>НОВАЯ ЗАЯВКА НА УБОРКУ</b>\n\n"
        f"👤 Имя: {data.get('name')}\n"
        f"📞 Телефон: {data.get('phone')}\n"
        f"📍 Адрес: {data.get('address')}\n"
        f"🏠 Тип: {data.get('room_type')}\n"
        f"📐 Площадь: {data.get('area')} м²\n"
        f"🧹 Уборка: {data.get('cleaning_type')}\n"
        f"📅 Дата: {data.get('date')}\n"
    )

    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
    except Exception as e:
        print(f"⚠️ Ошибка отправки админу: {e}")

    await callback.message.edit_text(
        "✅ <b>Заявка принята!</b>\n\n"
        "Спасибо! Наш менеджер свяжется с вами в течение 15 минут для подтверждения.",
        parse_mode="HTML"
    )

    # Очищаем состояние
    await state.clear()
    await callback.answer()


# ============================================
# 9. КОНТАКТЫ
# ============================================python CleanRU_Pro_Bot.py
@dp.callback_query(F.data == "contacts")
async def contacts(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать в Telegram", url="https://t.me/CleanRU_Support")],
            [InlineKeyboardButton(text="🌐 Наш сайт", url="https://cleanru.ru")],
            [InlineKeyboardButton(text="💬 Написать в Telegram", url="https://t.me/CleanruSupport")],
            [InlineKeyboardButton(text="📋 Главное меню", callback_data="menu")],
        ]
    )

    await callback.message.edit_text(
        "📞 <b>Связаться с нами</b>\n\n"
        "Телефон: +7 (999) 123-45-67\n"
        "Telegram: @CleanruSupport\n"
        "Email: info@cleanru.ru\n\n"
        "Режим работы: ежедневно с 8:00 до 22:00",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================
# 10. ВОЗВРАТ В ГЛАВНОЕ МЕНЮ
# ============================================
@dp.callback_query(F.data == "menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧮 Рассчитать стоимость", callback_data="calc")],
            [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="order")],
            [InlineKeyboardButton(text="❓ Частые вопросы", callback_data="faq")],
            [InlineKeyboardButton(text="📞 Связаться с нами", callback_data="contacts")],
        ]
    )

    await callback.message.edit_text(
        "🧹 <b>Cleanru — Помощник</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================
# 11. ЗАПУСК
# ============================================
async def main():
    print("🧹 Бот Cleanru запущен!")
    print("📋 Готов помогать с уборкой!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())