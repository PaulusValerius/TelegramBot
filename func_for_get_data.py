import aiosqlite
import json
import aiofiles

#Функция для создания базы данных с таблицей для хранения информации по опросу
async def create_table():
    async with aiosqlite.connect("box_quiz.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER, count_of_right INTEGER)")
        await db.commit()

#Функция для обнуления информации в таблице при начале нового опроса
async def insert_quiz(user_id, index, correct_question):
    async with aiosqlite.connect("box_quiz.db") as db:
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index,count_of_right) VALUES (?, ?, ?)', (user_id, index,correct_question))
        await db.commit()

#Функция для обновления информации в таблице при прохождении запроса. 
#Два SQL запроса в зависимости от того верен ли был ответ или нет. Если ответ был верен увеличивает счетсик верныз ответов
async def update_quiz_information(user_id, index, mode = False):
    async with aiosqlite.connect("box_quiz.db") as db:
        if not mode:
            await db.execute(f'UPDATE quiz_state SET question_index = {index} WHERE user_id = {user_id}')
            await db.commit()
        if mode:
            await db.execute(f'UPDATE quiz_state SET question_index = {index}, count_of_right = count_of_right + 1 WHERE user_id = {user_id}')
            await db.commit()

#Получение количества верных ответов из таблицы.
async def get_stat(user_id):
    async with aiosqlite.connect("box_quiz.db") as db:
        async with db.execute('SELECT count_of_right FROM quiz_state WHERE user_id = (?)', (user_id,)) as cursor:
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0

#Получение текущего запроса из таблицы.
async def get_quiz_index(user_id):
    async with aiosqlite.connect("box_quiz.db") as db:
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id,)) as cursor:
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0

#Функия загрузки из файла JSON списка вопросов            
async def load_questions(file_name):
    data = None
    async with aiofiles.open(file_name,'r') as file:
       data = await file.read()
       data = json.loads(data) 
    return data