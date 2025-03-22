from func_for_get_data import *
from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
#from Bot import quiz_data
#Создает фоновую клавиатуру в теле чата по вариантам ответа.
def generate_keyboard(answer_options, correct_answer):
    builder = InlineKeyboardBuilder()
    for option in answer_options:
        builder.add(types.InlineKeyboardButton(text = option, callback_data="Верный ответ" if option == correct_answer
                                               else "Неверный ответ"))
    builder.adjust(1)
    return builder.as_markup()

#Получает индекс текущего вопроса из базы данных и создает клавиатуру с клавишей по каждому ответу.
async def get_question(message, user_id, quiz_data : list):
    current_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_index]['correct_option']
    opts = quiz_data[current_index]['options']
    kb = generate_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_index]['question']}" , reply_markup=kb)

#Функия для начала опроса. Обнуляет счетчик статистики и текущего вопроса в базе данных. И начинает опрос.
async def new_questions(message: types.Message, quiz_data : list):
    user_id = message.from_user.id
    current_index = 0
    correct_question = 0
    await insert_quiz(user_id, current_index, correct_question)
    await get_question(message, user_id, quiz_data)

#Класс асинхронного счетчика для асинхронного прохода по циклу. Нужен для удаления существующих клавиатур 
# в теле бота при остановке или начале нового опроса.
class Asyncrange:
    class __asyncrange:
        def __init__(self, *args):
            self.__iter_range = iter(range(1,*args))

        async def __anext__(self):
            try:
                return next(self.__iter_range)
            except StopIteration as e:
                raise StopAsyncIteration(str(e))

    def __init__(self, *args):
        self.__args = args

    def __aiter__(self):
        return self.__asyncrange(*self.__args)