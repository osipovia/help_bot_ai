"""
LLM клиент для работы с OpenRouter API.

Использует бесплатную модель qwen/qwen3-14b:free для генерации
человекоподобных ответов в контексте консультации по услугам.
"""

import httpx
import json
from pathlib import Path
from typing import List, Dict, Optional
from src.config.settings import settings, logger
from .logger import llm_logger


class LLMClient:
    """Клиент для работы с OpenRouter API"""
    
    def __init__(self):
        """Инициализация LLM клиента с настройками OpenRouter"""
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "qwen/qwen3-14b:free"  # Бесплатная модель 14.8B параметров
        self.headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://help-bot-ai.local",
            "X-Title": "Help Bot AI - Drone Academy Consultant"
        }
        
        # Загружаем системный промпт из файла
        self.system_prompt = self._load_system_prompt()
        
        logger.info(f"🤖 LLM клиент инициализирован. Модель: {self.model}")
        logger.info(f"📝 Системный промпт загружен ({len(self.system_prompt)} символов)")
        
    def _load_system_prompt(self) -> str:
        """Загружает системный промпт из файла data/system_prompt.txt"""
        try:
            prompt_path = Path(__file__).parent.parent.parent / "data" / "system_prompt.txt"
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read().strip()
            
            if not prompt:
                raise ValueError("Системный промпт пустой")
                
            return prompt
            
        except FileNotFoundError:
            logger.error("❌ Файл system_prompt.txt не найден")
            return self._get_fallback_prompt()
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки системного промпта: {e}")
            return self._get_fallback_prompt()
    
    def _get_fallback_prompt(self) -> str:
        """Возвращает базовый промпт если основной файл недоступен"""
        return (
            "Ты консультант компании 'Академия дронов'. "
            "Помогаешь клиентам выбрать подходящие курсы и услуги. "
            "Будь дружелюбным и профессиональным. "
            "Отвечай только о наших услугах по дронам."
        )

    async def generate_response(
        self, 
        user_message: str,
        found_services: str = "",
        conversation_history: Optional[List[Dict]] = None,
        user_id: str = "unknown"
    ) -> str:
        """
        Генерирует ответ через OpenRouter API с детальным логгированием
        
        Args:
            user_message: Сообщение пользователя
            found_services: Найденные услуги из базы знаний (контекст для RAG)
            conversation_history: История диалога (список dict с role/content)
            user_id: ID пользователя для логгирования
            
        Returns:
            str: Ответ от LLM модели
        """
        
        # Формируем полный системный промпт с контекстом услуг
        full_system_prompt = self.system_prompt
        if found_services:
            full_system_prompt += f"\n\nДОСТУПНЫЕ УСЛУГИ:\n{found_services}"
        
        # Формируем список сообщений для API
        messages = [{"role": "system", "content": full_system_prompt}]
        
        # Добавляем историю диалога (последние 5 сообщений для экономии токенов)
        if conversation_history:
            messages.extend(conversation_history[-5:])
            
        # Добавляем текущее сообщение пользователя  
        messages.append({"role": "user", "content": user_message})
        
        # Начинаем детальное логгирование запроса
        request_context = llm_logger.start_request(
            user_id=user_id,
            model=self.model,
            messages=messages,
            found_services=found_services,
            conversation_history=conversation_history
        )
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7,  # Баланс креативности/точности
                        "max_tokens": 800,   # Ограничиваем длину ответа
                        "top_p": 0.9        # Nucleus sampling для качества
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Извлекаем ответ модели
                assistant_message = data["choices"][0]["message"]["content"]
                
                # Логгируем успешный ответ через детальный логгер
                llm_logger.log_success(request_context, data, assistant_message)
                
                return assistant_message.strip()
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", "")
            except:
                error_detail = e.response.text
            
            # Логгируем HTTP ошибку через детальный логгер
            llm_logger.log_error(
                request_context, 
                "http_error", 
                f"HTTP {e.response.status_code}: {error_detail}"
            )
            
            # Возвращаем fallback сообщение
            return (
                "😔 Извините, сейчас у меня технические проблемы с ИИ-помощником. "
                "Могу предложить связаться с нашим менеджером для консультации."
            )
            
        except httpx.TimeoutException:
            # Логгируем таймаут через детальный логгер
            llm_logger.log_error(request_context, "timeout", "Превышено время ожидания ответа API")
            
            return (
                "⏰ Извините, запрос занимает слишком много времени. "
                "Попробуйте переформулировать вопрос или обратитесь к менеджеру."
            )
            
        except Exception as e:
            # Логгируем неожиданную ошибку через детальный логгер
            llm_logger.log_error(
                request_context, 
                "unexpected_error", 
                f"{type(e).__name__}: {str(e)}"
            )
            
            return (
                "😔 Извините, произошла техническая ошибка. "
                "Обратитесь к нашему менеджеру для получения помощи."
            )
    
    def _prepare_fallback_response(self, error_type: str) -> str:
        """Подготавливает fallback ответ в зависимости от типа ошибки"""
        fallbacks = {
            "rate_limit": (
                "🚦 Сейчас очень много запросов к ИИ-помощнику. "
                "Попробуйте через минуту или обратитесь к менеджеру."
            ),
            "model_error": (
                "🤖 ИИ-помощник временно недоступен. "
                "Могу предложить связаться с нашим менеджером."
            ),
            "network": (
                "🌐 Проблемы с соединением. "
                "Проверьте интернет или обратитесь к менеджеру."
            )
        }
        
        return fallbacks.get(error_type, fallbacks["model_error"])


# Создаем глобальный экземпляр для использования в handlers
llm_client = LLMClient() 