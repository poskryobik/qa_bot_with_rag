from handlers.markup import main_keyboard
from aiogram.utils.formatting import Text, Bold
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Router, F




router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """
        Обращение по имени
    """
    content = Text("Приветствую Вас, ", Bold(message.from_user.full_name), "!")
    await message.answer(**content.as_kwargs(),
                         reply_markup=main_keyboard())


@router.message(F.text)
async def message_with_text(message: Message):
    """
        В случае ввода какого либо сообщения вывод возможных команд
    """
    await message.answer("""Команда не ясна.
Пожалуйста, попробуйте ввести одну из команд:
/start - начало работы
или выбирете из меню.
""",
    reply_markup=main_keyboard())


@router.message(F.sticker)
async def message_with_sticker(message: Message):
    """
        Информирование что прислали стикер
    """
    await message.answer("""Стикер не является командой.
Пожалуйста, введите команду.""")


@router.message(F.animation)
async def message_with_gif(message: Message):
    """
        Информирование что прислали GIF
    """
    await message.answer("""GIF не является командой.
Пожалуйста, введите команду.""")


@router.message(F.photo)
async def message_with_photo(message: Message):
    """
        Информирование что прислали изображение
    """
    await message.answer("""Изображение не является командой.
Пожалуйста, введите команду""")
