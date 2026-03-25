"""
Telegram-бот "Пандора" - AI Терапевт-помощник
==============================================
Гибридный бот психологической поддержки с двумя режимами работы:
1. Базовые ответы из intents.json для простых запросов
2. AI-генерация через Meta-Llama 3.3 70B для сложных диалогов

Технологии:
- aiogram 3.x - асинхронная работа с Telegram API
- OpenAI SDK - подключение к AI
- difflib - нечеткое сопоставление текстовых паттернов
"""

import os
import json
import random
import asyncio
import time
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from difflib import get_close_matches
from dotenv import load_dotenv
from openai import OpenAI


# КОНФИГУРАЦИЯ И ИНИЦИАЛИЗАЦИЯ
# Загрузка переменных окружения из .env файла
load_dotenv()

# API ключи для Telegram бота и AI
BOT_TOKEN = '8456744219:AAEq_AWH1rfEz_PGtuLmjdQj34wbcJq2DXI'
API_KEY = '595cdf7e-da8e-443f-b27d-73fc62125245'
AI_BASE_URL = 'https://api.sambanova.ai/v1'
AI_MODEL = 'Meta-Llama-3.3-70B-Instruct'

# Инициализация бота и диспетчера событий
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Попытка подключения к AI сервису
try:
    ai_client = OpenAI(
        base_url=AI_BASE_URL,
        api_key=API_KEY
    )
    AI_ENABLED = True
except:
    AI_ENABLED = False
    print("AI отключен. Работаем только с intents.json")

# Словарь для хранения истории диалогов каждого пользователя
conversation_history = {}

# Максимальное количество пар сообщений в истории
MAX_HISTORY = 8



# СОЗДАНИЕ ИНЛАЙН-КЛАВИАТУРЫ
def get_inline_menu() -> InlineKeyboardMarkup:
    """
    Инлайн-меню для приветственного сообщения
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Начать разговор", callback_data="start_talk")
        ],
        [
            InlineKeyboardButton(text="🧘 Упражнения", callback_data="exercises")
        ],
        [
            InlineKeyboardButton(text="📞 Телефон доверия", callback_data="hotline")
        ],
        [
            InlineKeyboardButton(text="🌟 Оценить бота", callback_data="rate_bot")
        ],
        [
            InlineKeyboardButton(text="❓ Что я умею?", callback_data="help")
        ]
    ])
    return keyboard


# ЗАГРУЗКА БАЗЫ ИНТЕНТОВ
with open("intents.json", "r", encoding="utf-8") as f:
    intents_data = json.load(f)

intents_list = intents_data["intents"]
intent_map = {intent["tag"]: intent for intent in intents_list}


# ========================================
# СИСТЕМА СБОРА СТАТИСТИКИ ПОЛЬЗОВАТЕЛЕЙ
# ========================================

# Файл для хранения статистики
STATS_FILE = "user_stats.json"

# Словарь для хранения активных сеансов (в оперативной памяти)
# Ключ - user_id, значение - время начала сеанса
active_sessions = {}


def load_stats() -> dict:
    """
    📂 ФУНКЦИЯ ЗАГРУЗКИ СТАТИСТИКИ
    
    Эта функция загружает данные из файла user_stats.json.
    
    КАК РАБОТАЕТ:
    1. Пытается открыть файл user_stats.json
    2. Если файл существует - загружает данные
    3. Если файла нет - создает начальную структуру
    
    ВОЗВРАЩАЕТ: словарь (dict) со статистикой
    """
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Если файл не найден, создаем начальную структуру (упрощенная)
        return {
            "users": {},
            "global_stats": {
                "total_users": 0,
                "total_messages": 0
            }
        }
    except json.JSONDecodeError:
        # Если файл поврежден, создаем новую структуру
        print("⚠️ Файл статистики поврежден, создаю новый")
        return {
            "users": {},
            "global_stats": {
                "total_users": 0,
                "total_messages": 0
            }
        }


def save_stats(stats: dict):
    """
    💾 ФУНКЦИЯ СОХРАНЕНИЯ СТАТИСТИКИ
    
    Эта функция сохраняет статистику в файл user_stats.json.
    
    ПАРАМЕТРЫ:
    - stats: словарь с данными статистики
    
    КАК РАБОТАЕТ:
    1. Открывает файл user_stats.json для записи
    2. Сохраняет данные в формате JSON с отступами (красиво форматированный)
    3. ensure_ascii=False позволяет сохранять кириллицу
    """
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Ошибка сохранения статистики: {e}")


def initialize_user(stats: dict, user_id: int, username: str, first_name: str):
    """
    👤 ФУНКЦИЯ ИНИЦИАЛИЗАЦИИ НОВОГО ПОЛЬЗОВАТЕЛЯ
    
    Создает запись для нового пользователя в базе статистики.
    
    ПАРАМЕТРЫ:
    - stats: словарь статистики
    - user_id: ID пользователя в Telegram
    - username: username пользователя (@username)
    - first_name: имя пользователя
    
    КАК РАБОТАЕТ:
    1. Проверяет, есть ли уже такой пользователь
    2. Если нет - создает новую запись с базовыми полями
    3. Увеличивает счетчик общих пользователей
    """
    user_id_str = str(user_id)
    
    if user_id_str not in stats["users"]:
        # Создаем новую запись пользователя (только базовая информация)
        stats["users"][user_id_str] = {
            "user_id": user_id,
            "username": username or "Не указан",
            "first_name": first_name or "Не указано",
            "first_interaction": datetime.now().isoformat(),
            "last_interaction": datetime.now().isoformat(),
            "total_messages": 0,
            "ai_requests_count": 0,
            "ratings": []
        }
        
        # Увеличиваем счетчик глобальных пользователей
        stats["global_stats"]["total_users"] += 1
        
        print(f"✅ Инициализирован новый пользователь: {user_id} ({first_name})")


def start_session(user_id: int):
    """
    🚀 ФУНКЦИЯ НАЧАЛА СЕАНСА (УПРОЩЕННАЯ)
    
    Запускает новый сеанс работы пользователя с ботом.
    
    ПАРАМЕТРЫ:
    - user_id: ID пользователя
    
    КАК РАБОТАЕТ:
    Сохраняет только время начала сеанса для проверки таймаута.
    """
    active_sessions[user_id] = {
        "start_time": time.time()
    }
    print(f"🚀 Начат сеанс для пользователя {user_id}")


def end_session(stats: dict, user_id: int):
    """
    🏁 ФУНКЦИЯ ОКОНЧАНИЯ СЕАНСА (УПРОЩЕННАЯ)
    
    Завершает сеанс пользователя.
    
    ПАРАМЕТРЫ:
    - stats: словарь статистики
    - user_id: ID пользователя
    
    КАК РАБОТАЕТ:
    Просто удаляет сеанс из активных без сохранения детальной информации.
    """
    if user_id in active_sessions:
        session_data = active_sessions[user_id]
        end_time = time.time()
        duration = end_time - session_data["start_time"]
        
        # Удаляем из активных сеансов
        del active_sessions[user_id]
        
        print(f"🏁 Завершен сеанс для пользователя {user_id}. Продолжительность: {round(duration/60, 2)} минут")


def track_message(stats: dict, user_id: int, is_ai: bool = False):
    """
    📨 ФУНКЦИЯ ОТСЛЕЖИВАНИЯ СООБЩЕНИЯ (УПРОЩЕННАЯ)
    
    Записывает базовую статистику сообщений пользователя.
    
    ПАРАМЕТРЫ:
    - stats: словарь статистики
    - user_id: ID пользователя
    - is_ai: было ли это обращение к AI (True/False)
    
    КАК РАБОТАЕТ:
    1. Обновляет время последнего взаимодействия
    2. Увеличивает счетчик сообщений пользователя
    3. Если использовался AI - увеличивает счетчик AI-запросов
    """
    user_id_str = str(user_id)
    
    if user_id_str in stats["users"]:
        # Обновляем время последнего взаимодействия
        stats["users"][user_id_str]["last_interaction"] = datetime.now().isoformat()
        
        # Увеличиваем счетчик сообщений
        stats["users"][user_id_str]["total_messages"] += 1
        stats["global_stats"]["total_messages"] += 1
        
        # Если использовался AI
        if is_ai:
            stats["users"][user_id_str]["ai_requests_count"] += 1


def add_satisfaction_rating(stats: dict, user_id: int, rating: int):
    """
    ⭐ ФУНКЦИЯ ДОБАВЛЕНИЯ ОЦЕНКИ БОТА
    
    Сохраняет оценку пользователя в user_stats.json.
    
    ПАРАМЕТРЫ:
    - stats: словарь статистики
    - user_id: ID пользователя
    - rating: оценка от 1 до 10
    """
    user_id_str = str(user_id)
    
    if user_id_str in stats["users"]:
        # Инициализируем список оценок если его нет
        if "ratings" not in stats["users"][user_id_str]:
            stats["users"][user_id_str]["ratings"] = []
        
        # Добавляем новую оценку с временной меткой
        stats["users"][user_id_str]["ratings"].append({
            "rating": rating,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"⭐ Получена оценка {rating}/10 от пользователя {user_id}")
        save_stats(stats)


def check_session_timeout(stats: dict):
    """
    ⏰ ФУНКЦИЯ ПРОВЕРКИ ТАЙМАУТА СЕАНСОВ
    
    Автоматически закрывает сеансы, которые неактивны более 30 минут.
    
    ПАРАМЕТРЫ:
    - stats: словарь статистики
    
    КАК РАБОТАЕТ:
    1. Проходит по всем активным сеансам
    2. Проверяет, сколько времени прошло с последней активности
    3. Если прошло более 30 минут (1800 секунд) - закрывает сеанс
    
    ВАЖНО: Эта функция будет вызываться при каждом новом сообщении,
    чтобы автоматически закрывать забытые сеансы.
    """
    SESSION_TIMEOUT = 1800  # 30 минут в секундах
    current_time = time.time()
    
    sessions_to_end = []
    
    for user_id, session_data in active_sessions.items():
        # Если прошло более 30 минут с начала сеанса и нет активности
        if current_time - session_data["start_time"] > SESSION_TIMEOUT:
            sessions_to_end.append(user_id)
    
    # Завершаем устаревшие сеансы
    for user_id in sessions_to_end:
        end_session(stats, user_id)
        print(f"⏰ Автоматически завершен неактивный сеанс пользователя {user_id}")



# ФУНКЦИЯ ОПРЕДЕЛЕНИЯ ИНТЕНТА
def find_best_intent(user_message: str) -> str | None:
    """
    Определяет интент (намерение) пользователя по его сообщению.
    """
    user_message = user_message.strip().lower()

    if not user_message:
        return "нет_ответа"

    # ШАГ 1: ТОЧНОЕ СОВПАДЕНИЕ
    for intent in intents_list:
        for pattern in intent["patterns"]:
            if pattern and pattern.lower() == user_message:
                return intent["tag"]

    # ШАГ 2: НЕЧЕТКОЕ СОВПАДЕНИЕ
    all_patterns = []
    pattern_to_tag = {}

    for intent in intents_list:
        for pattern in intent["patterns"]:
            if pattern and pattern.strip():
                p = pattern.lower()
                all_patterns.append(p)
                pattern_to_tag[p] = intent["tag"]

    if not all_patterns:
        return "нет_ответа"

    matches = get_close_matches(user_message, all_patterns, n=1, cutoff=0.6)

    if matches:
        return pattern_to_tag[matches[0]]

    return None


# ФУНКЦИЯ AI-ГЕНЕРАЦИИ ОТВЕТОВ
def get_ai_response(user_id: int, user_message: str) -> str:
    """
    Генерирует ответ с помощью AI модели Meta-Llama 3.3 70B.
    """
    if not AI_ENABLED:
        return "AI недоступен. Используйте команды из базы."

    try:
        if user_id not in conversation_history:
            conversation_history[user_id] = []

        conversation_history[user_id].append({
            "role": "user",
            "content": user_message
        })

        if len(conversation_history[user_id]) > MAX_HISTORY * 2:
            conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY * 2:]

        system_prompt = """Ты Пандора - эмпатичный психолог-терапевт.
Слушай внимательно, задавай открытые вопросы, поддерживай и помогай решить проблему.
Отвечай кратко (2-3 предложения), по-доброму, на русском.
Используй контекст предыдущих сообщений."""

        messages = [{"role": "system", "content": system_prompt}] + conversation_history[user_id]

        response = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )

        ai_answer = response.choices[0].message.content

        conversation_history[user_id].append({
            "role": "assistant",
            "content": ai_answer
        })

        return ai_answer

    except Exception as e:
        print(f"Ошибка AI: {e}")
        return "Извините, возникла техническая проблема. Попробуйте ещё раз."


# ОБРАБОТЧИК КОМАНДЫ /START
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    """
    Обработчик команды /start.
    
    📊 СБОР СТАТИСТИКИ:
    - Инициализируем нового пользователя
    - Начинаем новый сеанс
    - Отслеживаем использование команды /start
    """
    # Загружаем статистику
    stats = load_stats()
    
    # Инициализируем пользователя, если он новый
    initialize_user(
        stats,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    # Начинаем новый сеанс
    start_session(message.from_user.id)
    
    # Сохраняем статистику
    save_stats(stats)
    
    welcome_text = (
        "👋 *Привет! Я Пандора* — ваш терапевтический ИИ-помощник\n\n"
        "🌸 Я помогу вам:\n"
        "• Поговорить о чувствах и эмоциях\n"
        "• Отслеживать настроение\n"
        "• Освоить упражнения для релаксации\n"
        "• Вести дневник эмоций\n\n"
        "Выберите нужное действие:"
    )
    await message.answer(
        welcome_text,
        reply_markup=get_inline_menu(),
        parse_mode="Markdown"
    )





# ОБРАБОТЧИК КНОПКИ "ОЦЕНИТЬ БОТА"
@dp.callback_query(F.data == "rate_bot")
async def callback_rate_bot(callback: types.CallbackQuery):
    """
    🌟 Показывает меню оценки бота от 1 до 10
    """
    # Создаем клавиатуру с оценками от 1 до 10
    rating_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data="rate_1"),
            InlineKeyboardButton(text="2", callback_data="rate_2"),
            InlineKeyboardButton(text="3", callback_data="rate_3"),
            InlineKeyboardButton(text="4", callback_data="rate_4"),
            InlineKeyboardButton(text="5", callback_data="rate_5")
        ],
        [
            InlineKeyboardButton(text="6", callback_data="rate_6"),
            InlineKeyboardButton(text="7", callback_data="rate_7"),
            InlineKeyboardButton(text="8", callback_data="rate_8"),
            InlineKeyboardButton(text="9", callback_data="rate_9"),
            InlineKeyboardButton(text="10", callback_data="rate_10")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_menu")
        ]
    ])
    
    await callback.message.edit_text(
        "🌟 *Оцените работу бота*\n\n"
        "Ваше мнение очень важно!\n"
        "Выберите оценку от 1 до 10:",
        reply_markup=rating_keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


# ОБРАБОТЧИК ОЦЕНОК
@dp.callback_query(F.data.startswith("rate_"))
async def callback_rating(callback: types.CallbackQuery):
    """
    ⭐ ОБРАБОТЧИК ОЦЕНОК БОТА
    
    Сохраняет оценку пользователя в user_stats.json.
    """
    # Извлекаем оценку из callback_data
    rating = int(callback.data.split("_")[1])
    
    # Загружаем статистику
    stats = load_stats()
    
    # Инициализируем пользователя если новый
    initialize_user(
        stats,
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    
    # Добавляем оценку
    add_satisfaction_rating(stats, callback.from_user.id, rating)
    
    # Формируем ответ в зависимости от оценки
    if rating >= 8:
        response_text = (
            f"⭐ *Спасибо за высокую оценку {rating}/10!*\n\n"
            "Я рад, что смог вам помочь! 🌸\n"
            "Продолжайте обращаться ко мне, когда понадобится поддержка."
        )
    elif rating >= 5:
        response_text = (
            f"⭐ *Спасибо за оценку {rating}/10*\n\n"
            "Я стараюсь стать лучше.\n"
            "Если у вас есть предложения по улучшению - напишите мне!"
        )
    else:
        response_text = (
            f"⭐ *Спасибо за оценку {rating}/10*\n\n"
            "Мне жаль, что я не смог помочь должным образом.\n"
            "Пожалуйста, напишите, что можно улучшить!"
        )
    
    await callback.message.edit_text(
        response_text,
        parse_mode="Markdown"
    )
    await callback.answer("✅ Оценка сохранена")


# ОБРАБОТЧИКИ ИНЛАЙН-КНОПОК
@dp.callback_query(F.data == "start_talk")
async def callback_start_talk(callback: types.CallbackQuery):
    """� Начать разговор с ботом"""
    await callback.message.edit_text(
        "💬 Отлично! Расскажите, как вы себя чувствуете сегодня?\n\n"
        "Можете писать о своих переживаниях, мыслях или просто о том, что на душе.",
        reply_markup=None
    )
    await callback.answer()


@dp.callback_query(F.data == "exercises")
async def callback_exercises(callback: types.CallbackQuery):
    """🧘 Меню упражнений"""
    exercises_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌬️ Дыхательная практика", callback_data="ex_breathing")],
        [InlineKeyboardButton(text="🧘 Медитация 5 минут", callback_data="ex_meditation")],
        [InlineKeyboardButton(text="💪 Мышечная релаксация", callback_data="ex_relaxation")],
        [InlineKeyboardButton(text="🎯 Заземление 5-4-3-2-1", callback_data="ex_grounding")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_menu")]
    ])
    await callback.message.edit_text(
        "🧘 *Упражнения для релаксации*\n\n"
        "Выберите практику, которая вам нужна сейчас:",
        reply_markup=exercises_keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "ex_breathing")
async def callback_ex_breathing(callback: types.CallbackQuery):
    """🌬️ Дыхательная практика"""
    await callback.message.edit_text(
        "🌬️ *Дыхательная техника 4-7-8*\n\n"
        "1️⃣ Вдохните через нос на *4* счета\n"
        "2️⃣ Задержите дыхание на *7* счетов\n"
        "3️⃣ Выдохните через рот на *8* счетов\n\n"
        "Повторите 4-5 раз. Эта техника успокаивает нервную систему.\n\n"
        "💡 Совет: Делайте медленно, без спешки",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ К упражнениям", callback_data="exercises")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "ex_meditation")
async def callback_ex_meditation(callback: types.CallbackQuery):
    """🧘 Медитация"""
    await callback.message.edit_text(
        "🧘 *Медитация осознанности (5 минут)*\n\n"
        "1️⃣ Сядьте удобно, закройте глаза\n"
        "2️⃣ Сосредоточьтесь на дыхании\n"
        "3️⃣ Когда ум блуждает - мягко возвращайте внимание к дыханию\n"
        "4️⃣ Не судите себя за отвлечения\n"
        "5️⃣ Просто наблюдайте за вдохом и выдохом\n\n"
        "⏱️ Начните с 5 минут, постепенно увеличивайте время",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ К упражнениям", callback_data="exercises")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "ex_relaxation")
async def callback_ex_relaxation(callback: types.CallbackQuery):
    """� Мышечная релаксация"""
    await callback.message.edit_text(
        "💪 *Прогрессивная мышечная релаксация*\n\n"
        "Напрягите и расслабьте каждую группу мышц:\n\n"
        "1️⃣ Кулаки - сожмите (5 сек), расслабьте\n"
        "2️⃣ Руки - напрягите бицепсы, расслабьте\n"
        "3️⃣ Плечи - поднимите к ушам, опустите\n"
        "4️⃣ Лицо - наморщите, расслабьте\n"
        "5️⃣ Живот - втяните, отпустите\n"
        "6️⃣ Ноги - напрягите, расслабьте\n\n"
        "Почувствуйте разницу между напряжением и расслаблением",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ К упражнениям", callback_data="exercises")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "ex_grounding")
async def callback_ex_grounding(callback: types.CallbackQuery):
    """🎯 Заземление"""
    await callback.message.edit_text(
        "🎯 *Техника заземления 5-4-3-2-1*\n\n"
        "Назовите вокруг себя:\n"
        "👁️ *5* вещей, которые вы ВИДИТЕ\n"
        "✋ *4* вещи, которых можете КОСНУТЬСЯ\n"
        "👂 *3* звука, которые СЛЫШИТЕ\n"
        "👃 *2* запаха, которые ЧУВСТВУЕТЕ\n"
        "👅 *1* вкус во рту\n\n"
        "Эта практика помогает вернуться в настоящий момент при тревоге.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ К упражнениям", callback_data="exercises")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()



@dp.callback_query(F.data == "hotline")
async def callback_hotline(callback: types.CallbackQuery):
    """� Телефон доверия"""
    await callback.message.edit_text(
        "📞 *Телефон доверия*\n\n"
        "🔴 *8-800-2000-122*\n\n"
        "Единый общероссийский номер для детей, подростков и родителей\n\n"
        "⏰ Круглосуточно и бесплатно\n"
        "🤝 Квалифицированные психологи\n"
        "🔒 Анонимность гарантирована\n\n"
        "Не стесняйтесь обращаться! 💪",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_menu")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "help")
async def callback_help(callback: types.CallbackQuery):
    """❓ Информация о возможностях бота"""
    await callback.message.edit_text(
        "❓ *Мои возможности*\n\n"
        "💬 *Разговор* - общайтесь со мной о своих переживаниях\n"
        "📊 *Трекинг настроения* - отслеживайте эмоции\n"
        "🧘 *Упражнения* - техники релаксации и дыхания\n"
        "📖 *Дневник* - записывайте мысли\n\n"
        "🤖 Я использую AI для глубоких диалогов и базу знаний "
        "для быстрых ответов.\n\n"
        "⚠️ *Важно:* Я не заменяю профессионального психолога!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_menu")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "back_menu")
async def callback_back_menu(callback: types.CallbackQuery):
    """◀️ Возврат в главное меню"""
    await callback.message.edit_text(
        "👋 *Главное меню*\n\n"
        "🌸 Выберите нужное действие:",
        reply_markup=get_inline_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ГЛАВНЫЙ ОБРАБОТЧИК СООБЩЕНИЙ
@dp.message()
async def handle_message(message: types.Message):
    """
    Главный обработчик всех текстовых сообщений.
    
    📊 СБОР СТАТИСТИКИ:
    - Проверяем таймаут старых сеансов
    - Инициализируем пользователя если новый
    - Начинаем сеанс если не активен
    - Отслеживаем каждое сообщение
    - Записываем использованные интенты
    - Фиксируем обращения к AI
    """
    user_text = message.text or ""
    user_id = message.from_user.id
    
    # Загружаем статистику
    stats = load_stats()
    
    # Проверяем таймаут старых сеансов
    check_session_timeout(stats)
    
    # Инициализируем пользователя, если он новый
    initialize_user(
        stats,
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    # Начинаем новый сеанс, если он не активен
    if user_id not in active_sessions:
        start_session(user_id)

    # Если пользователь представляется
    if any(user_text.lower().startswith(pat.lower()) for pat in ["Меня зовут ", "Я - ", "Меня называют "]):
        for pat in ["Меня зовут ", "Я - ", "Меня называют "]:
            if user_text.lower().startswith(pat.lower()):
                name = user_text[len(pat):].strip()
                if name and "имя" in intent_map:
                    response = random.choice(intent_map["имя"]["responses"])
                    
                    # Отслеживаем сообщение без интента
                    track_message(stats, user_id, is_ai=False)
                    save_stats(stats)
                    
                    await message.answer(response)
                    return

    # ОПРЕДЕЛЕНИЕ ИНТЕНТА
    tag = find_best_intent(user_text)

    # Список простых интентов
    simple_intents = ["приветствие", "прощание", "благодарность", "утро", "день", "вечер", "ночь"]

    # Флаг использования AI
    used_ai = False
    
    # ГЕНЕРАЦИЯ ОТВЕТА
    if tag and tag in simple_intents and tag in intent_map:
        response = random.choice(intent_map[tag]["responses"])
    elif tag and tag in intent_map:
        response = random.choice(intent_map[tag]["responses"])
    else:
        if AI_ENABLED:
            response = get_ai_response(user_id, user_text)
            used_ai = True
        else:
            fallback = intent_map.get("нет_ответа", {"responses": ["Извините, я не понял."]})
            response = random.choice(fallback["responses"])
            tag = "нет_ответа"
    
    # Отслеживаем сообщение с информацией об использовании AI
    track_message(stats, user_id, is_ai=used_ai)
    save_stats(stats)

    await message.answer(response)


# ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА
async def main():
    """
    Точка входа в приложение.
    """
    print("🤖 Пандора - бот запущен")

    if AI_ENABLED:
        print("✓ AI режим активен")
    else:
        print("⚠ AI выключен, работаем с intents.json")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

