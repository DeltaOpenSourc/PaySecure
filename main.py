import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiohttp

TOKEN = "7954621147:AAGXHf_bsa2GmgoNbh7NGM8WofXf0daVWck"


bot = Bot(token=TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    waiting_for_fio = State()
    waiting_for_phone = State()


@dp.message(CommandStart())
async def command_brone_handler(message: Message) -> None:
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
          [InlineKeyboardButton(text="Анкета", callback_data="deepSeek")]
        ]
        
        
    )
    await message.answer(
        text=(
            "Приветствуем вас, мы работаем как платёжный посредник для клиентов, которым нужно оплачивать инвойсы за автомобили, оборудование и другие товары в разные страны. "
        ),
        reply_markup=markup,
    )


@dp.callback_query(lambda c: c.data == "deepSeek")
async def start_form(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите ФИО:")
    await state.set_state(Form.waiting_for_fio)
    await call.answer()


@dp.message(Form.waiting_for_fio)
async def process_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await message.answer("Спасибо! Теперь введите юзер-нейм:")
    await state.set_state(Form.waiting_for_phone)


@dp.message(Form.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Заявка составлена, ожидайте")

    data = await state.get_data()
    fio = data.get("fio")
    phone = data.get("phone")

    payload = {
        "fio": fio,
        "phone": phone,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("https://nexthe-beta.vercel.app/api/search", json=payload) as resp:
                if resp.status == 200:
                    response_json = await resp.json()
                    await message.answer(f"Ответ сервера:\n{response_json}")
                else:
                    await message.answer(f"Ошибка при запросе к серверу: {resp.status}")
        except Exception as e:
            await message.answer(f"Ошибка при выполнении запроса: {e}")

    await state.clear()


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
