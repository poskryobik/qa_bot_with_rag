from aiogram.types import ReplyKeyboardMarkup, KeyboardButton




def main_keyboard() -> ReplyKeyboardMarkup:
    """
        Формирование клавиатуры для главного меню
    """
    kb = [[
            KeyboardButton(text="Задать вопрос боту 💬"),
            KeyboardButton(text="Загрузить документ в БД 📤")
        ]
    ]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard