"""
Детальное логгирование LLM запросов и аналитика использования.

Реализует расширенное логгирование для мониторинга производительности
и качества ответов OpenRouter API согласно принципам KISS.
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from src.config.settings import logger


@dataclass
class LLMRequestMetrics:
    """Метрики одного LLM запроса"""
    timestamp: str
    user_id: str
    model: str
    request_size_chars: int
    messages_count: int
    has_context: bool
    has_history: bool
    
    # Метрики ответа
    response_time_ms: float
    success: bool
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    # Детали ошибки (если есть)
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    
    # Качество ответа
    response_length_chars: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует метрики в словарь для логгирования"""
        return asdict(self)


class LLMLogger:
    """Логгер для детального мониторинга LLM запросов"""
    
    def __init__(self):
        """Инициализация с настройками логгирования"""
        self.log_full_content = False  # Для production лучше False (privacy)
        self.metrics_history: List[LLMRequestMetrics] = []
        self.max_history_size = 100  # Последние 100 запросов
        
        logger.info("📊 LLM Logger инициализирован")
    
    def start_request(self, user_id: str, model: str, messages: List[Dict], 
                     found_services: str = "", conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Начинает логгирование LLM запроса
        
        Args:
            user_id: ID пользователя
            model: Модель LLM
            messages: Сообщения для API
            found_services: Найденные услуги (контекст)
            conversation_history: История диалога
            
        Returns:
            Контекст запроса для завершения логгирования
        """
        request_context = {
            "start_time": time.time(),
            "user_id": user_id,
            "model": model,
            "messages_count": len(messages),
            "request_size_chars": sum(len(msg.get("content", "")) for msg in messages),
            "has_context": bool(found_services.strip()),
            "has_history": bool(conversation_history),
            "timestamp": datetime.now().isoformat()
        }
        
        # Детальное логгирование (опционально)
        if self.log_full_content:
            logger.info(f"📤 LLM Full Request для {user_id}:")
            logger.info(f"  Модель: {model}")
            logger.info(f"  Сообщений: {len(messages)}")
            logger.info(f"  Контекст услуг: {len(found_services)} символов")
            if conversation_history:
                logger.info(f"  История: {len(conversation_history)} сообщений")
            logger.info(f"  Полный запрос: {json.dumps(messages, ensure_ascii=False, indent=2)}")
        else:
            # Краткое логгирование для production
            context_info = []
            if found_services.strip():
                context_info.append(f"услуги:{len(found_services)}ч")
            if conversation_history:
                context_info.append(f"история:{len(conversation_history)}м")
            
            context_str = f" [{','.join(context_info)}]" if context_info else ""
            
            logger.info(
                f"📤 LLM запрос {user_id}: {model}, "
                f"{len(messages)}сообщ, {request_context['request_size_chars']}симв{context_str}"
            )
        
        return request_context
    
    def log_success(self, request_context: Dict[str, Any], 
                   response_data: Dict[str, Any], assistant_message: str):
        """
        Логгирует успешный LLM ответ
        
        Args:
            request_context: Контекст запроса из start_request
            response_data: Полный ответ от API
            assistant_message: Сгенерированное сообщение
        """
        response_time_ms = (time.time() - request_context["start_time"]) * 1000
        usage = response_data.get("usage", {})
        
        # Создаем метрики
        metrics = LLMRequestMetrics(
            timestamp=request_context["timestamp"],
            user_id=request_context["user_id"],
            model=request_context["model"],
            request_size_chars=request_context["request_size_chars"],
            messages_count=request_context["messages_count"],
            has_context=request_context["has_context"],
            has_history=request_context["has_history"],
            response_time_ms=response_time_ms,
            success=True,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            response_length_chars=len(assistant_message)
        )
        
        # Сохраняем в историю
        self._save_metrics(metrics)
        
        # Детальное логгирование успеха
        if self.log_full_content:
            logger.info(f"📥 LLM Full Response для {metrics.user_id}:")
            logger.info(f"  Время ответа: {response_time_ms:.1f}мс")
            logger.info(f"  Токены: {metrics.prompt_tokens}+{metrics.completion_tokens}={metrics.total_tokens}")
            logger.info(f"  Ответ: {assistant_message}")
        else:
            # Краткое логгирование
            logger.info(
                f"📥 LLM успех {metrics.user_id}: "
                f"{response_time_ms:.0f}мс, {metrics.completion_tokens}токенов, "
                f"{metrics.response_length_chars}символов"
            )
        
        # Предупреждения о производительности
        if response_time_ms > 10000:  # > 10 секунд
            logger.warning(f"🐌 Медленный LLM ответ: {response_time_ms:.1f}мс для {metrics.user_id}")
        
        if metrics.total_tokens > 3000:  # Много токенов
            logger.warning(f"🔥 Высокое потребление токенов: {metrics.total_tokens} для {metrics.user_id}")
    
    def log_error(self, request_context: Dict[str, Any], 
                 error_type: str, error_message: str):
        """
        Логгирует ошибку LLM запроса
        
        Args:
            request_context: Контекст запроса из start_request
            error_type: Тип ошибки (http_error, timeout, network, etc.)
            error_message: Сообщение об ошибке
        """
        response_time_ms = (time.time() - request_context["start_time"]) * 1000
        
        # Создаем метрики ошибки
        metrics = LLMRequestMetrics(
            timestamp=request_context["timestamp"],
            user_id=request_context["user_id"],
            model=request_context["model"],
            request_size_chars=request_context["request_size_chars"],
            messages_count=request_context["messages_count"],
            has_context=request_context["has_context"],
            has_history=request_context["has_history"],
            response_time_ms=response_time_ms,
            success=False,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            error_type=error_type,
            error_message=error_message[:200]  # Обрезаем длинные ошибки
        )
        
        # Сохраняем в историю
        self._save_metrics(metrics)
        
        # Логгируем ошибку
        logger.error(
            f"❌ LLM ошибка {metrics.user_id}: {error_type} "
            f"через {response_time_ms:.0f}мс - {error_message[:100]}"
        )
    
    def _save_metrics(self, metrics: LLMRequestMetrics):
        """Сохраняет метрики в историю с ограничением размера"""
        self.metrics_history.append(metrics)
        
        # Ограничиваем размер истории
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Получает статистику использования LLM за период
        
        Args:
            hours: Период в часах для анализа
            
        Returns:
            Словарь со статистикой
        """
        if not self.metrics_history:
            return {"error": "Нет данных для анализа"}
        
        # Фильтруем метрики по времени
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        recent_metrics = [
            m for m in self.metrics_history 
            if datetime.fromisoformat(m.timestamp).timestamp() > cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": f"Нет данных за последние {hours} часов"}
        
        # Вычисляем статистику
        total_requests = len(recent_metrics)
        successful_requests = sum(1 for m in recent_metrics if m.success)
        failed_requests = total_requests - successful_requests
        
        success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
        
        # Средние метрики для успешных запросов
        successful_metrics = [m for m in recent_metrics if m.success]
        if successful_metrics:
            avg_response_time = sum(m.response_time_ms for m in successful_metrics) / len(successful_metrics)
            avg_tokens = sum(m.total_tokens for m in successful_metrics) / len(successful_metrics)
            total_tokens_used = sum(m.total_tokens for m in successful_metrics)
        else:
            avg_response_time = avg_tokens = total_tokens_used = 0
        
        # Подсчет ошибок по типам
        error_types = {}
        for m in recent_metrics:
            if not m.success and m.error_type:
                error_types[m.error_type] = error_types.get(m.error_type, 0) + 1
        
        # Уникальные пользователи
        unique_users = len(set(m.user_id for m in recent_metrics))
        
        stats = {
            "period_hours": hours,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate_percent": round(success_rate, 1),
            "unique_users": unique_users,
            "avg_response_time_ms": round(avg_response_time, 1) if avg_response_time else 0,
            "avg_tokens_per_request": round(avg_tokens, 1) if avg_tokens else 0,
            "total_tokens_used": total_tokens_used,
            "error_breakdown": error_types,
            "requests_with_context": sum(1 for m in recent_metrics if m.has_context),
            "requests_with_history": sum(1 for m in recent_metrics if m.has_history)
        }
        
        logger.info(f"📊 LLM статистика за {hours}ч: {stats}")
        return stats
    
    def enable_full_logging(self, enabled: bool = True):
        """Включает/выключает полное логгирование содержимого"""
        self.log_full_content = enabled
        status = "включено" if enabled else "выключено"
        logger.info(f"🔍 Полное логгирование LLM: {status}")


# Глобальный экземпляр для использования в LLM клиенте
llm_logger = LLMLogger() 