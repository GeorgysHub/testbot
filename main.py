import asyncio
import logging
import sys
import sqlite3
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import TOKEN

#Connect to DB
conn = sqlite3.connect("tasks.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS tasks
(user_id INTEGER, task_text TEXT)''')

dp = Dispatcher()
user_tasks = {}  #Словарь для задач пользователей
HELP_COMMAND = """
/help - список команд
/start - начать работу бота
/newTask - добавить задачу
/editTask - редактировать текст задачи
/allTasks - показать все задачи
/timer - напоминание для задачи
/deleteTask - удаление задачи
/deleteAll - удалить все задачи
"""
storage = MemoryStorage()

request_notifications_button = KeyboardButton(text='🔔Разрешить уведомления🔔')
help_button = KeyboardButton(text='❓Помощь❓')
allTask = KeyboardButton(text='📂Показать задачи📂')
addTask = KeyboardButton(text='✅Добавить задачу✅')
deleteAll = KeyboardButton(text='🗑Удалить всё🗑')
deleteTask = KeyboardButton(text='❌Удалить задачу❌')
keyboard = ReplyKeyboardMarkup(keyboard=[
    [request_notifications_button, addTask, deleteAll],
    [help_button, allTask, deleteTask]
],
    resize_keyboard=True)


def add_task(user_id, task_text):
    c.execute("INSERT INTO tasks (user_id, task_text) VALUES (?, ?)", (user_id, task_text))
    conn.commit()


async def fetch_tasks(user_id):
    c.execute("SELECT task_text FROM tasks WHERE user_id = ?", (user_id,))
    return c.fetchall()


class TaskStates(StatesGroup):
    newTask = State()
    waitingForDelete = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")
    await message.answer("Привет! Нажми на кнопку ниже, чтобы разрешить уведомления.", reply_markup=keyboard)


@dp.message(lambda message: message.text == '🔔Разрешить уведомления🔔')
async def allow_notification(message: Message) -> None:
    await message.answer("Запрос на включение уведомлений отправлен.")


@dp.message(lambda message: message.text == '❓Помощь❓')
async def help_command(message: Message) -> None:
    await message.reply(text=HELP_COMMAND)


@dp.message(lambda message: message.text == '✅Добавить задачу✅')
async def new_task_command(message: Message, state=FSMContext) -> None:
    await message.answer("Хорошо, запиши и отправь мне, то что нужно запомнить :)")
    await state.set_state(TaskStates.newTask)


@dp.message(StateFilter(TaskStates.newTask))
async def process_task(message: Message, state: FSMContext) -> None:
    task_text = message.text
    add_task(message.from_user.id, task_text)
    await message.answer(f"Задачи '{task_text}' успешно записана ;)")
    await state.clear()


@dp.message(lambda message: message.text == '📂Показать задачи📂')
async def get_tasks(message: Message) -> None:
    user_id = message.from_user.id
    tasks = await fetch_tasks(user_id)
    if tasks:
        task_texts = [f"{index + 1}. {task[0]}" for index, task in enumerate(tasks)]
        await message.answer("Твои задачи :\n" + "\n".join(task_texts))
    else:
        await message.answer("На данный момент у вас нет добавленных задач")


@dp.message(lambda message: message.text == '🗑Удалить всё🗑')
async def delete_all_tasks(message: Message) -> None:
    user_id = message.from_user.id
    c.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
    conn.commit()
    await message.answer("Все задачи успешно удалены")


@dp.message(lambda message: message.text == '❌Удалить задачу❌')
async def delete_task(message: Message, state: FSMContext) -> None:
    await message.answer("Выберите номер задачи, которую вы хотите убрать")
    await state.set_state(TaskStates.waitingForDelete)


@dp.message(StateFilter(TaskStates.waitingForDelete))
async def process_task_to_delete(message: Message, state: FSMContext):
    user_id = message.from_user.id
    task_number = message.text
    tasks = await fetch_tasks(user_id)
    if task_number.isdigit() and 1 <= int(task_number) <= len(tasks):
        task_index = int(task_number) - 1
        task_to_delete = tasks[task_index][0]
        with conn:
            c.execute("DELETE FROM tasks WHERE user_id = ? AND task_text = ?", (user_id, task_to_delete))
            conn.commit()
        await message.answer(f"Задача '{task_to_delete}' успешно удалена.")
    else:
        await message.answer("Некорректный номер задачи. Попробуйте еще раз.")
    await state.clear()


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stdout)
    asyncio.run(main())
