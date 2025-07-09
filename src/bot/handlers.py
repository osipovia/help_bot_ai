from aiogram import Router, types
from aiogram.filters import Command
from src.config.settings import logger
from src.knowledge.search import KnowledgeSearcher
from src.llm.client import llm_client
from src.llm.logger import llm_logger
from .states import dialog_manager

# Создаем роутер для обработки сообщений
router = Router()

# Инициализируем поисковик знаний один раз при загрузке модуля
knowledge_searcher = KnowledgeSearcher()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    """Обработчик команды /start с описанием возможностей поиска"""
    user_id = str(message.from_user.id)
    user_name = message.from_user.full_name
    
    logger.info(f"Команда /start от пользователя {user_id} ({user_name})")
    
    # Сохраняем команду /start в историю
    dialog_manager.add_message(user_id, "user", "/start")
    
    welcome_text = (
        "🎯 Привет! Я ваш персональный консультант Академии дронов.\n\n"
        "💫 Я умею:\n"
        "• Подбирать курсы под ваши цели и опыт\n"
        "• Рассказывать детали о программах обучения\n"
        "• Помогать с записью и оплатой\n"
        "• Консультировать по корпоративным мероприятиям\n\n"
        "🚁 Просто расскажите, что вас интересует:\n"
        "• 'Хочу научиться управлять дроном'\n"
        "• 'Ищу курсы для ребенка'\n"
        "• 'Нужно корпоративное мероприятие'\n\n"
        "Задавайте любые вопросы! 🚁✨"
    )
    
    await message.answer(welcome_text)
    
    # Сохраняем приветствие в историю диалога
    dialog_manager.add_message(user_id, "assistant", welcome_text)
    
    logger.info(f"Приветствие с описанием возможностей отправлено пользователю {user_id}")


@router.message(Command("stats"))
async def stats_handler(message: types.Message):
    """Обработчик команды /stats для отображения статистики LLM"""
    user_id = str(message.from_user.id)
    user_name = message.from_user.full_name
    
    logger.info(f"Команда /stats от пользователя {user_id} ({user_name})")
    
    try:
        # Получаем статистику за последние 24 часа
        stats = llm_logger.get_statistics(hours=24)
        
        if "error" in stats:
            await message.answer(f"📊 {stats['error']}")
            return
        
        # Форматируем статистику для отображения
        stats_text = (
            "📊 <b>Статистика LLM за последние 24 часа</b>\n\n"
            f"🔢 Всего запросов: <b>{stats['total_requests']}</b>\n"
            f"✅ Успешных: <b>{stats['successful_requests']}</b>\n"
            f"❌ Ошибок: <b>{stats['failed_requests']}</b>\n"
            f"📈 Успешность: <b>{stats['success_rate_percent']}%</b>\n\n"
            f"👥 Уникальных пользователей: <b>{stats['unique_users']}</b>\n"
            f"⏱️ Среднее время ответа: <b>{stats['avg_response_time_ms']}мс</b>\n"
            f"🎯 Токенов на запрос: <b>{stats['avg_tokens_per_request']}</b>\n"
            f"🔥 Всего токенов: <b>{stats['total_tokens_used']}</b>\n\n"
            f"🎯 С контекстом услуг: <b>{stats['requests_with_context']}</b>\n"
            f"📚 С историей диалога: <b>{stats['requests_with_history']}</b>"
        )
        
        # Добавляем информацию об ошибках если есть
        if stats['error_breakdown']:
            stats_text += "\n\n❌ <b>Типы ошибок:</b>\n"
            for error_type, count in stats['error_breakdown'].items():
                stats_text += f"• {error_type}: {count}\n"
        
        await message.answer(stats_text, parse_mode="HTML")
        
        # Сохраняем команду в историю диалога
        dialog_manager.add_message(user_id, "user", "/stats")
        dialog_manager.add_message(user_id, "assistant", stats_text)
        
        logger.info(f"Статистика LLM отправлена пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики для пользователя {user_id}: {e}")
        await message.answer("😔 Ошибка получения статистики. Попробуйте позже.")


@router.message()
async def smart_consultation_handler(message: types.Message):
    """RAG-консультация: поиск + LLM генерация умного ответа с историей диалога"""
    user_id = str(message.from_user.id)
    user_name = message.from_user.full_name
    query = message.text or ""
    
    logger.info(f"💬 RAG-консультация от пользователя {user_id} ({user_name}): '{query}'")
    
    # Проверяем, что это текстовое сообщение
    if not query.strip():
        await message.answer("🤔 Пожалуйста, напишите текстовый запрос для консультации.")
        return
    
    # Сохраняем сообщение пользователя в историю диалога
    dialog_manager.add_message(user_id, "user", query)
    
    try:
        # Шаг 1: Поиск релевантных услуг в базе знаний
        search_results = knowledge_searcher.search(query, limit=3)
        logger.info(f"🔍 Найдено услуг: {len(search_results)}")
        
        # Шаг 2: Форматируем найденную информацию для LLM контекста
        if search_results:
            services_context_parts = []
            for service in search_results:
                # Получаем детальную информацию об услуге
                details = knowledge_searcher.get_service_details(service['id'])
                
                service_info = f"Услуга: {service['name']}\n"
                service_info += f"Категория: {service['category']}\n"
                service_info += f"Цена: {service['price']}\n"
                service_info += f"Код курса: {service['courseCode']}\n"
                
                if details and details.get('full_description'):
                    service_info += f"Описание: {details['full_description']}\n"
                
                if details and details.get('details'):
                    service_info += f"Детали: {details['details']}\n"
                
                service_info += f"Релевантность: {service['relevance_score']}%"
                services_context_parts.append(service_info)
            
            services_context = "\n\n".join(services_context_parts)
        else:
            services_context = "Подходящие услуги не найдены в базе знаний."
        
        logger.info(f"📄 Контекст для LLM: {len(services_context)} символов")
        
        # Получаем историю диалога для контекста
        conversation_history = dialog_manager.get_conversation_history(user_id, limit=5)
        
        # Шаг 3: Генерируем умный ответ через LLM с RAG контекстом и историей
        response = await llm_client.generate_response(
            user_message=query,
            found_services=services_context,
            conversation_history=conversation_history,
            user_id=user_id
        )
        
        # Шаг 4: Отправляем персонализированный ответ пользователю
        await message.answer(response, parse_mode="HTML")
        
        # Сохраняем ответ бота в историю диалога
        dialog_manager.add_message(user_id, "assistant", response)
        
        logger.info(f"✅ RAG-ответ успешно отправлен пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка RAG-консультации для пользователя {user_id}: {e}")
        
        # Fallback: используем простой поиск без LLM
        try:
            logger.info(f"🔄 Fallback: простой поиск для пользователя {user_id}")
            fallback_response = knowledge_searcher.search_and_format_for_telegram(query)
            await message.answer(fallback_response, parse_mode="HTML")
            
        except Exception as fallback_error:
            logger.error(f"❌ Fallback тоже failed для пользователя {user_id}: {fallback_error}")
            
            error_response = (
                "😔 Извините, сейчас у меня технические проблемы.\n"
                "Обратитесь к нашему менеджеру для персональной консультации."
            )
            await message.answer(error_response)


def register_handlers(dp):
    """Регистрация всех обработчиков в диспетчере"""
    logger.info("📝 Регистрация обработчиков сообщений с поиском знаний")
    dp.include_router(router)
    logger.info("✅ Обработчики с KnowledgeSearcher зарегистрированы") 