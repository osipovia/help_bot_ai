from aiogram import Router, types
from aiogram.filters import Command
from src.config.settings import logger
from src.knowledge.search import KnowledgeSearcher

# Создаем роутер для обработки сообщений
router = Router()

# Инициализируем поисковик знаний один раз при загрузке модуля
knowledge_searcher = KnowledgeSearcher()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    """Обработчик команды /start с описанием возможностей поиска"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    logger.info(f"Команда /start от пользователя {user_id} ({user_name})")
    
    welcome_text = (
        "🎯 Привет! Я Help Bot AI - ассистент Академии дронов.\n\n"
        "Я помогу найти подходящие курсы и услуги! Просто напишите:\n"
        "• 'курсы дронов'\n"
        "• 'обучение FPV'\n" 
        "• 'корпоративное обучение'\n"
        "• 'индивидуальные занятия'\n"
        "• или любой другой запрос\n\n"
        "Попробуйте спросить что-то! 🚁"
    )
    
    await message.answer(welcome_text)
    logger.info(f"Приветствие с описанием возможностей отправлено пользователю {user_id}")


@router.message()
async def smart_search_handler(message: types.Message):
    """Умный поиск услуг по запросу пользователя"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    query = message.text or ""
    
    logger.info(f"Поиск от пользователя {user_id} ({user_name}): '{query}'")
    
    # Проверяем, что это текстовое сообщение
    if not query.strip():
        await message.answer("🤔 Пожалуйста, напишите текстовый запрос для поиска услуг.")
        return
    
    try:
        # Выполняем поиск и форматирование результатов для Telegram
        response = knowledge_searcher.search_and_format_for_telegram(query)
        
        # Отправляем результаты с HTML форматированием для эмодзи
        await message.answer(response, parse_mode="HTML")
        
        logger.info(f"Результаты поиска успешно отправлены пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка поиска для пользователя {user_id}: {e}")
        
        error_response = (
            "😔 Извините, произошла ошибка при поиске.\n"
            "Попробуйте переформулировать запрос или обратитесь позже."
        )
        await message.answer(error_response)


def register_handlers(dp):
    """Регистрация всех обработчиков в диспетчере"""
    logger.info("📝 Регистрация обработчиков сообщений с поиском знаний")
    dp.include_router(router)
    logger.info("✅ Обработчики с KnowledgeSearcher зарегистрированы") 