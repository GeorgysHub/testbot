import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from config import TOKEN

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


class TaskStates(StatesGroup):
    newTask = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")
    await message.delete()


@dp.message(Command(commands=["help"]))
async def help_command(message: Message) -> None:
    await message.reply(text=HELP_COMMAND)
    await message.delete()


@dp.message(Command(commands=["newTask"]))
async def new_task_command(message: Message, state=FSMContext) -> None:
    await message.answer("Хорошо, запиши и отправь мне, то что нужно запомнить :)")
    await state.set_state(TaskStates.newTask)


@dp.message(StateFilter(TaskStates.newTask))
async def process_task(message: Message, state: FSMContext) -> None:
    task_text = message.text
    user_tasks[message.from_user.id] = task_text
    await message.answer(f"Задачи '{task_text}' успешно записана ;)")
    await state.clear()


@dp.message(Command(commands=["allTasks"]))
async def get_tasks(message: Message) -> None:
    user_id = message.from_user.id
    task = user_tasks.get(user_id)
    if task:
        await message.answer("Твои задачи :" + task)
    else:
        await message.answer("На данный момент у вас нет добавленных задач")


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
