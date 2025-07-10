import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiohttp
import aiosqlite
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_ID = 5108832503

async def setup_database():
    async with aiosqlite.connect('database.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS derty (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
        await db.commit()

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    waiting_for_fio = State()
    waiting_for_service_choice = State()
    waiting_for_username = State()
    waiting_for_phone = State()

class AdminForm(StatesGroup):
    waiting_for_action = State()
    waiting_for_new_service_name = State()
    waiting_for_service_to_delete = State()

@dp.message(CommandStart())
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Анкета", callback_data="deepSeek")],
        [InlineKeyboardButton(text="Связь с менеджером", url="https://t.me/Paysecure1")]
    ])
    await message.answer(
        "Приветствуем вас, мы работаем как платёжный посредник для клиентов, которым нужно оплачивать инвойсы за автомобили, оборудование и другие товары в разные страны.",
        reply_markup=kb,
    )

@dp.callback_query(lambda c: c.data == "deepSeek")
async def ask_fio(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите ФИО:")
    await state.set_state(Form.waiting_for_fio)
    await call.answer()

async def TernerTerner():
    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute('SELECT name FROM derty')
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def services_keyboard():
    services = await TernerTerner()
    kb_builder = InlineKeyboardBuilder()
    for service in services:
        kb_builder.button(text=service, callback_data=f"service_{service}")
    kb_builder.adjust(1)
    return kb_builder.as_markup()

@dp.message(Form.waiting_for_fio)
async def process_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)
    
    kb = await services_keyboard()
    if kb.inline_keyboard:
        await message.answer("Выберите услугу:", reply_markup=kb)
    else:
        await message.answer("Пока нет доступных услуг. Обратитесь к администратору.")
        await state.clear()
        return
    await state.set_state(Form.waiting_for_service_choice)

@dp.callback_query(lambda c: c.data and c.data.startswith("service_"), StateFilter(Form.waiting_for_service_choice))
async def process_service_choice(call: CallbackQuery, state: FSMContext):
    service = call.data[len("service_"):]
    await state.update_data(service=service)
    await call.message.answer(f"Ваша услуга: {service}")
    await call.message.answer("Введите ваш юзернейм:")
    await state.set_state(Form.waiting_for_username)
    await call.answer()

@dp.message(Form.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.answer("Введите ваш номер телефона:")
    await state.set_state(Form.waiting_for_phone)

@dp.message(Form.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    await message.answer("Заявка успешно отправлена! Введите /start для начала заново.")
    fio = data.get("fio")
    username = data.get("username")
    phone = data.get("phone")
    service = data.get("service")

    await state.clear()

    payload = {
        "fio": fio,
        "username": username,
        "phone": phone,
        "service": service,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://nexthe-beta.vercel.app/api/search", json=payload) as resp:
            if resp.status == 200:
                await message.answer("Заявка успешно отправлена! Введите /start для начала заново.")
            else:
                await message.answer("Ошибка при отправке заявки. Попробуйте позже.")

@dp.message(Command(commands=["admin"]))
async def admin_panel(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет доступа к этой команде.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить услугу", callback_data="admin_add")],
        [InlineKeyboardButton(text="Удалить услугу", callback_data="admin_delete")],
    ])
    await message.answer("Панель администратора. Выберите действие:", reply_markup=kb)
    await state.set_state(AdminForm.waiting_for_action)

@dp.callback_query(lambda c: c.data and c.data.startswith("admin_"))
async def admin_actions(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Доступ запрещён", show_alert=True)
        return

    action = call.data[len("admin_"):]

    if action == "add":
        await state.set_state(AdminForm.waiting_for_new_service_name)
        await call.message.answer("Введите название услуги для добавления:")
        await call.answer()

    elif action == "delete":
        await state.set_state(AdminForm.waiting_for_service_to_delete)
        await call.message.answer("Введите название услуги для удаления:")
        await call.answer()

@dp.message(AdminForm.waiting_for_new_service_name)
async def process_for_name(message: Message, state: FSMContext):
    service_name = message.text.strip()
    async with aiosqlite.connect('database.db') as db:
        try:
            await db.execute('INSERT INTO derty (name) VALUES (?)', (service_name,))
            await db.commit()
            await message.answer(f"Услуга '{service_name}' добавлена в базу данных.")
            ferty = await TernerTerner()
            await message.answer("\n".join(f"{i+1}. {service}" for i, service in enumerate(ferty)))
        except aiosqlite.IntegrityError:
            await message.answer(f"Услуга '{service_name}' уже существует в базе.")
    await state.clear()

@dp.message(AdminForm.waiting_for_service_to_delete)
async def process_for_delete(message: Message, state: FSMContext):
    service_name = message.text.strip()
    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute('DELETE FROM derty WHERE name = ?', (service_name,))
        await db.commit()
        await message.answer(f"Услуга '{service_name}' удалена из базы данных.")
        ferty = await TernerTerner()
        await message.answer("\n".join(f"{i+1}. {service}" for i, service in enumerate(ferty)))
    await state.clear()

async def main():
    await setup_database()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
