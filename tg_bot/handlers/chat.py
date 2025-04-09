from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from handlers.markup import main_keyboard
from aiogram import Router, F, Bot
from aiogram.types import Message
import requests
import os




router = Router()

class Reccom(StatesGroup):
    """
        Stage group
    """
    choosing_action = State()
    make_query = State()
    add_document = State()


@router.message(F.text == "Задать вопрос боту 💬")
async def msg_cmd_reccom(message: Message, state: FSMContext):
    await message.answer(
        text="Введите вопрос:"
    )
    await state.set_state(Reccom.make_query)


@router.message(F.text == "Загрузить документ в БД 📤")
async def document_upload(message: Message, state: FSMContext):
    await message.answer(
        text="Загрузите word документ:"
    )
    await state.set_state(Reccom.add_document)


@router.message(Reccom.make_query)
async def llm_query(message: Message, state: FSMContext):
    """
        Ответ LLM
    """
    await message.answer(text="Думаю...")
    llm_api_url = os.getenv("LLM_API_URL") + "/generate"
    response = requests.post(llm_api_url,
                            json={"query": message.text})
    response_data = response.json()
    response_text = response_data["response"]
    response_text = (response_text.strip('"\n')
                     .replace(".", "\.")
                     .replace("-", "\-")
                     .replace("(", "\(")
                     .replace(")", "\)")
                     .replace("!", "\!")
                     .replace("*", "")
                     )

    await message.answer(text=response_text,
                         reply_markup=main_keyboard(), 
                         parse_mode="MarkdownV2")
    await state.clear()

    
@router.message(Reccom.add_document)
async def doc_load(message: Message, state: FSMContext, bot: Bot):
    """
        Загрузить документ в векторную базу данных через API
    """
    
    file_id = message.document.file_id
    file_name = message.document.file_name
    file = await bot.get_file(file_id)
    file_path = file.file_path
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"

    # load file
    response = requests.get(file_url)
    if response.status_code == 200:
        file_content = response.content

        # Отправляем файл в API
        api_url = os.getenv("FAISS_API_URL") + "/add-documents" # "http://faiss_api:8000/add-documents"
        files = {'files': (file_name, file_content)}
        await message.answer(text="Приступил к загрузке документа. Пожалуйста, подождите.")
        api_response = requests.post(api_url, files=files)

        if api_response.status_code == 200:
            await message.answer(text="Документ успешно загружен в векторную базу данных!",
                                 reply_markup=main_keyboard())
        else:
            await message.answer(text="Ошибка при загрузке документа в API.",
                                 reply_markup=main_keyboard())
    else:
        await message.answer(text="Не удалось скачать документ.",
                             reply_markup=main_keyboard())

    await state.clear()