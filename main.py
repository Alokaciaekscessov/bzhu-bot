import os 
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from engine import calculate_nutrition, save_to_csv


TOKEN = "8863929856:AAGrhqsQ-F1AVaNSJXrsOi8gly47oN4JqWM"
CSV_FILENAME = "result.csv"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Состояния для пошагового опроса (Машина состояний) 
class CalcStates(StatesGroup):
    waiting_for_weight = State()
    waiting_for_height = State()
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_activity = State()
    waiting_for_goal = State()

def get_main_keyboard(): 
    button = KeyboardButton(text="Скачать CSV отчет")
    keyboard = ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
    return keyboard

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    gender_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")]
    ], resize_keyboard=True, one_time_keyboard=True)

    await message.answer("Этот бот поможет рассчитать твою суточную норму калорий и БЖУ.\n Введите ваш пол:")
    await state.set_state(CalcStates.waiting_for_gender)    

# Получение пола
@dp.message(CalcStates.waiting_for_gender, F.text.in_(["Мужской", "Женский"]))
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text.lower()) # сохраняем "мужской" или "женский"
    await message.answer("Введите ваш возраст:")
    await state.set_state(CalcStates.waiting_for_age)

# Получение возраста
@dp.message(CalcStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("Пожалуйста, введите возраст числом.")
        return
    
    await state.update_data(age=int(message.text))
    await message.answer("Успешно! Теперь введите ваш вес в кг:")
    await state.set_state(CalcStates.waiting_for_weight)

# Получение веса 
@dp.message(CalcStates.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    if not message.text.isdigit():
       await message.answer("Введите число")
       return
    
    await state.update_data(weight=float(message.text))
    await message.answer("Теперь введите рост в см: ")
    await state.set_state(CalcStates.waiting_for_height)

@dp.message(CalcStates.waiting_for_height)
async def process_height(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("Пожалуйста введите число")
        return 
    
    await state.update_data(height=float(message.text))
    
    activity_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Малоподвижный (1.2)")],
        [KeyboardButton(text="Умеренный (1.375)")],
        [KeyboardButton(text="Активный (1.55)")]
    ], resize_keyboard=True, one_time_keyboard=True)
    
    await message.answer("Выберите уровень активности:", reply_markup=activity_kb)
    await state.set_state(CalcStates.waiting_for_activity)

@dp.message(CalcStates.waiting_for_activity)
async def process_activity(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста выберите активность")
        return
    
    coef = 1.2
    if "1.375" in message.text:
        coef = 1.375
    elif "1.55" in message.text:
        coef = 1.55
    
    await state.update_data(activity_coef=coef)
    
    goal_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Похудение"), KeyboardButton(text="Поддержание"), KeyboardButton(text="Набор массы")]
    ], resize_keyboard=True, one_time_keyboard=True)
    
    await message.answer("Выберите вашу цель:", reply_markup=goal_kb)
    await state.set_state(CalcStates.waiting_for_goal)


@dp.message(CalcStates.waiting_for_goal)
async def process_goal(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста выберите цель кнопками")
        return 

    goal = "поддержание"
    if "Похудение" in message.text:
        goal = "похудение"
    elif "Набор" in message.text:
        goal = "набор"  

    user_data = await state.get_data()
    age = user_data["age"]
    gender = user_data["gender"]
    weight = user_data["weight"]
    height = user_data["height"]
    coef = user_data["activity_coef"]    

    await state.clear()
    results = calculate_nutrition(
        weight=weight, 
        height=height, 
        age=age, 
        gender=gender, 
        activity_coef=coef,
        goal=goal
    )

    save_to_csv(weight, height, goal, results, CSV_FILENAME)

    response_text = (
        f"Ваш результат под цель: {message.text}\n\n"
        f"Пол: {gender.capitalize()} | Возраст: {age} лет \n"
        f"Рост: {height} см | Вес: {weight} кг \n"
        f"Суточная норма: {results['calories']} ккал \n\n"
        f"Норма БЖУ: \n"
        f"Белки: {results['proteins']} г \n"
        f"Жиры: {results['fats']} г \n"
        f"Углеводы: {results['carbs']} г \n"
    )
    await message.answer(response_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


@dp.message(F.text == "Скачать CSV отчет")
async def send_csv(message: Message):
    if os.path.exists(CSV_FILENAME):
        # Отправляем файл прямо в чат
        document = FSInputFile(CSV_FILENAME, filename="План_БЖУ.csv")
        await message.answer_document(document, caption="Вот ваш готовый отчет")
    else:
        await message.answer("Сначала пройдите расчет введите команду /start")

async def main():
    print("Бот успешно запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())