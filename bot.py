import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Configuration import with fallback
try:
    from config import BOT_TOKEN, API_URL
except ImportError as e:
    raise ImportError(
        "Создайте файл config.py с переменными BOT_TOKEN и API_URL\n"
        "или установите их как переменные окружения"
    ) from e

# Initialize bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# States
class AddTaskStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_deadline = State()

# Command handlers
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я бот для управления задачами.\n\n"
        "Доступные команды:\n"
        "/show_tasks - Показать задачи\n"
        "/add_task - Добавить задачу\n"
        "/delete_task - Удалить задачу"
    )

@dp.message(Command("show_tasks"))
async def show_tasks(message: types.Message):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/tasks") as resp:
                if resp.status == 200:
                    tasks = await resp.json()
                    if not tasks:
                        await message.answer("Список задач пуст")
                        return

                    response = "Ваши задачи:\n\n"
                    for task in tasks:
                        response += f"{task['name']}\nДедлайн: {task['deadline']}\n\n"
                    await message.answer(response)
                else:
                    await message.answer("Ошибка при получении задач")
    except Exception:
        await message.answer("Произошла ошибка")

@dp.message(Command("add_task"))
async def add_task(message: types.Message, state: FSMContext):
    await message.answer("Введите название задачи:")
    await state.set_state(AddTaskStates.waiting_for_name)

@dp.message(AddTaskStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите дедлайн (ДД.ММ.ГГГГ):")
    await state.set_state(AddTaskStates.waiting_for_deadline)

@dp.message(AddTaskStates.waiting_for_deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        task_data = {"name": data["name"], "deadline": message.text}

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_URL}/tasks", json=task_data) as resp:
                if resp.status == 200:
                    task = await resp.json()
                    await message.answer(
                        f"Задача добавлена!\nНазвание: {task['name']}\nДедлайн: {task['deadline']}"
                    )
                else:
                    error = await resp.text()
                    await message.answer(f"Ошибка: {error}")
    except Exception:
        await message.answer("Произошла ошибка")
    finally:
        await state.clear()

@dp.message(Command("delete_task"))
async def delete_task(message: types.Message):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/tasks") as resp:
                if resp.status == 200:
                    tasks = await resp.json()
                    if not tasks:
                        await message.answer("Список задач пуст")
                        return

                    builder = InlineKeyboardBuilder()
                    for task in tasks:
                        builder.button(
                            text=task['name'],
                            callback_data=f"delete_{task['id']}",
                        )
                    builder.adjust(1)
                    await message.answer(
                        "Выберите задачу для удаления:",
                        reply_markup=builder.as_markup()
                    )
                else:
                    await message.answer("Ошибка при получении задач")
    except Exception:
        await message.answer("Произошла ошибка")

@dp.callback_query(F.data.startswith("delete_"))
async def delete_callback(callback: types.CallbackQuery):
    task_id = callback.data.split("_")[1]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{API_URL}/tasks/{task_id}") as resp:
                if resp.status == 200:
                    async with session.get(f"{API_URL}/tasks") as resp:
                        if resp.status == 200:
                            tasks = await resp.json()
                            response = "Задача удалена\n\n"
                            if tasks:
                                response += "Оставшиеся задачи:\n\n"
                                for task in tasks:
                                    response += f"{task['name']}\nДедлайн: {task['deadline']}\n\n"
                            else:
                                response += "Список задач пуст"
                            await callback.message.edit_text(response)
                        else:
                            await callback.message.edit_text("Задача удалена")
                else:
                    error = await resp.text()
                    await callback.message.edit_text(f"Ошибка: {error}")
    except Exception:
        await callback.message.edit_text("Произошла ошибка")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())