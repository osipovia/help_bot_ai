import logging
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения с валидацией через Pydantic"""
    
    # Telegram Bot
    telegram_bot_token: str
    
    # OpenRouter API
    openrouter_api_key: str
    
    # 1C Integration
    onec_api_url: str
    onec_client_id: str
    onec_client_secret: str
    
    # Application Settings
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Настройка базового логгирования согласно conventions.md
    
    Args:
        log_level: Уровень логгирования (INFO, ERROR, DEBUG)
        
    Returns:
        Configured logger instance
    """
    # Настройка формата логов: timestamp, name, level, message
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()],
        force=True  # Переопределить существующую конфигурацию
    )
    
    # Создать и вернуть logger для приложения
    logger = logging.getLogger("help_bot_ai")
    logger.info(f"Логгирование настроено. Уровень: {log_level}")
    
    return logger


# Глобальные настройки приложения
try:
    settings = Settings()
    logger = setup_logging(settings.log_level)
    logger.info("Настройки приложения загружены успешно")
except Exception as e:
    # Fallback логгирование при ошибках конфигурации
    logging.basicConfig(level=logging.ERROR)
    logging.error(f"Ошибка загрузки настроек: {e}")
    raise 