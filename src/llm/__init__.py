"""
Модуль для работы с LLM (Large Language Models).

Обеспечивает интеграцию с OpenRouter API для генерации
человекоподобных ответов в консультационном боте.
"""

from .client import LLMClient
from .logger import LLMLogger, llm_logger

__all__ = ["LLMClient", "LLMLogger", "llm_logger"] 