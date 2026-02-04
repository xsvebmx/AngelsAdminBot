from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards import main_menu_kb


async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("⚡ Remnawave Admin Bot", reply_markup=main_menu_kb())
