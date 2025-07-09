import asyncio
from aiogram import Bot, Dispatcher
from src.config.settings import settings, logger
from src.bot.handlers import register_handlers


async def main():
    """Главная функция запуска Help Bot AI"""
    
    logger.info("🚀 Запуск Help Bot AI")
    
    # Создание экземпляра бота
    bot = Bot(token=settings.telegram_bot_token)
    
    # Создание диспетчера для обработки событий
    dp = Dispatcher()
    
    # Регистрация обработчиков сообщений
    register_handlers(dp)
    
    logger.info("✅ Бот запущен и готов к работе")
    
    try:
        # Запуск polling (опрос серверов Telegram)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка при работе бота: {e}")
        raise
    finally:
        logger.info("🛑 Бот остановлен")
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main()) 