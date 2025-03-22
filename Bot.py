import json
import asyncio
import logging
import aiofiles
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
import aiosqlite
from  aiogram import F
from func_for_bot import * 
from func_for_get_data import *
import nest_asyncio
nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)
API_TOKEN = "7053237014:AAEieEAQdo-BDOvB71q6WwQpcTbb74QtXOg"
my_bot = Bot(token=API_TOKEN)
dp = Dispatcher()
quiz_data :  list = None

#обработчик команды \Start. Создает обычную клавиатуру с 3 кнопками(Начать опрос. Остановить опрос. Показать статистику)
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text = "Начать опрос"), types.KeyboardButton(text= "Остановить опрос"), types.KeyboardButton(text ='Показать статистику'))
    await message.answer("Приветствую. Давайте пройдем опрос!", reply_markup = builder.as_markup(resize_keyboard = True))

#обработчик команды \statistict, или сообщения 'Показать статистику'. Получает количество 
# верных ответов из БД. Выводит на экран сообщение с процентом верных ответов. 
@dp.message(F.text == "Показать статистику")
@dp.message(Command('statistics'))
async def cmd_stat(message : types.Message):
    count_of_right = await get_stat(message.from_user.id)
    part = count_of_right / len(quiz_data)
    text = None
    if part !=0:
        text = f'Вы ответили верно на {part:.0%} вопросов!'
    else:
        text = 'Вы еще не ответили правильно ни на один вопрос!'
    await message.answer(text)

#обработчик команды \stop, или сообщения 'Остановить опрос'.
# Убирает все клавиатуры с вопросами из тела бота. 
@dp.message(F.text == "Остановить опрос")
@dp.message(Command('stop'))
async def cmd_stop(message: types.Message):
    async for i in Asyncrange(message.message_id):
        try:
            await my_bot.edit_message_reply_markup(
                chat_id=message.from_user.id,
                message_id=message.message_id-i,
                reply_markup=None
            )
        except TelegramBadRequest:
            pass
        except TelegramRetryAfter:
            pass
    await message.answer("Опрос остановлен")

#обработчик команды \quiz, или сообщения 'Начать опрос'.
# Убирает все cуществующие клавиатуры с вопросами из тела бота.
# Обнуляет весь опрос в базе данных.
@dp.message(F.text == "Начать опрос")
@dp.message(Command('quiz'))
async def cmd_quiz(message: types.Message):
    await message.answer("Начнем опрос:")
    await new_questions(message, quiz_data)
    async for i in Asyncrange(message.message_id):
        try:
            await my_bot.edit_message_reply_markup(
                chat_id=message.from_user.id,
                message_id=message.message_id - i,
                reply_markup=None
            )
        except TelegramBadRequest:
            pass
        except TelegramRetryAfter:
            pass

@dp.callback_query(F.data == "Верный ответ")
async def right_answer(callback: types.CallbackQuery):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']
    # Отправляем в чат сообщение, что ответ верный
    await callback.message.answer(f"Верно! - {quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_information(callback.from_user.id, current_question_index, True)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id, quiz_data)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer("Это был последний вопрос. Опрос Завершен!")

@dp.callback_query(F.data == "Неверный ответ")
async def wrong_answer(callback: types.CallbackQuery):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)

    correct_option = quiz_data[current_question_index]['correct_option']

    # Отправляем в чат сообщение об ошибке с указанием верного ответа
    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_information(callback.from_user.id, current_question_index)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id, quiz_data)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")

async def main():
    data_task = asyncio.create_task(load_questions('quize.json'))
    table_task = asyncio.create_task(create_table())
    global quiz_data
    quiz_data = await data_task
    await table_task
    await dp.start_polling(my_bot)

if __name__ == "__main__":
     asyncio.run(main())
    

    
    
    
    