"""
Управление состояниями диалогов в памяти.

Реализует простую систему состояний согласно vision.md:
- consultation: обычная консультация
- payment_request: сбор данных для оплаты  
- manager_request: передача менеджеру
"""

from datetime import datetime
from typing import Dict, List, Optional, Literal
from src.config.settings import logger

# Типы состояний диалога
DialogState = Literal["consultation", "payment_request", "manager_request", "error"]


class DialogStateManager:
    """Управление состояниями диалогов в памяти согласно принципам KISS"""
    
    def __init__(self):
        """Инициализация с пустым хранилищем сессий"""
        self.sessions: Dict[str, Dict] = {}
        logger.info("💬 DialogStateManager инициализирован")
    
    def get_session(self, user_id: str) -> Dict:
        """
        Получает или создает сессию пользователя
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            Словарь с данными сессии
        """
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "messages": [],
                "state": "consultation",
                "selected_course": None,
                "contact_name": None,
                "phone": None,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
            logger.info(f"👤 Создана новая сессия для пользователя {user_id}")
        else:
            # Обновляем время последней активности
            self.sessions[user_id]["last_activity"] = datetime.now().isoformat()
            
        return self.sessions[user_id]
    
    def add_message(self, user_id: str, role: str, content: str):
        """
        Добавляет сообщение в историю диалога
        
        Args:
            user_id: Идентификатор пользователя
            role: Роль отправителя (user, assistant)
            content: Содержимое сообщения
        """
        session = self.get_session(user_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        session["messages"].append(message)
        
        # Ограничиваем историю последними 20 сообщениями для экономии памяти
        if len(session["messages"]) > 20:
            session["messages"] = session["messages"][-20:]
            logger.info(f"📝 История сообщений обрезана для пользователя {user_id}")
        
        logger.info(f"💬 Добавлено сообщение {role} для пользователя {user_id}")
    
    def get_conversation_history(self, user_id: str, limit: int = 5) -> List[Dict]:
        """
        Получает историю сообщений для передачи в LLM
        
        Args:
            user_id: Идентификатор пользователя
            limit: Количество последних сообщений
            
        Returns:
            Список сообщений в формате для LLM (role, content)
        """
        session = self.get_session(user_id)
        messages = session["messages"][-limit:] if session["messages"] else []
        
        # Преобразуем в формат для LLM (убираем timestamp)
        llm_messages = [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in messages
        ]
        
        logger.info(f"📖 Возвращена история из {len(llm_messages)} сообщений для пользователя {user_id}")
        return llm_messages
    
    def set_state(self, user_id: str, state: DialogState):
        """
        Устанавливает состояние диалога
        
        Args:
            user_id: Идентификатор пользователя
            state: Новое состояние диалога
        """
        session = self.get_session(user_id)
        old_state = session["state"]
        session["state"] = state
        
        logger.info(f"🔄 Состояние пользователя {user_id}: {old_state} → {state}")
    
    def get_state(self, user_id: str) -> DialogState:
        """
        Получает текущее состояние диалога
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            Текущее состояние диалога
        """
        session = self.get_session(user_id)
        return session["state"]
    
    def set_selected_course(self, user_id: str, course_info: Dict):
        """
        Сохраняет выбранный курс
        
        Args:
            user_id: Идентификатор пользователя
            course_info: Информация о выбранном курсе
        """
        session = self.get_session(user_id)
        session["selected_course"] = course_info
        
        logger.info(f"📚 Выбранный курс для пользователя {user_id}: {course_info.get('name', 'Unknown')}")
    
    def set_contact_info(self, user_id: str, name: Optional[str] = None, phone: Optional[str] = None):
        """
        Сохраняет контактную информацию
        
        Args:
            user_id: Идентификатор пользователя
            name: ФИО клиента
            phone: Номер телефона
        """
        session = self.get_session(user_id)
        
        if name is not None:
            session["contact_name"] = name
            logger.info(f"👤 Имя для пользователя {user_id}: {name}")
            
        if phone is not None:
            session["phone"] = phone
            logger.info(f"📞 Телефон для пользователя {user_id}: {phone}")
    
    def get_contact_info(self, user_id: str) -> Dict[str, Optional[str]]:
        """
        Получает контактную информацию
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            Словарь с контактной информацией
        """
        session = self.get_session(user_id)
        return {
            "name": session.get("contact_name"),
            "phone": session.get("phone")
        }
    
    def clear_session(self, user_id: str):
        """
        Очищает сессию пользователя (для сброса диалога)
        
        Args:
            user_id: Идентификатор пользователя
        """
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"🗑️ Сессия пользователя {user_id} очищена")
    
    def get_session_stats(self) -> Dict:
        """
        Получает статистику активных сессий
        
        Returns:
            Словарь со статистикой
        """
        total_sessions = len(self.sessions)
        states_count = {}
        
        for session in self.sessions.values():
            state = session["state"]
            states_count[state] = states_count.get(state, 0) + 1
        
        stats = {
            "total_sessions": total_sessions,
            "states_distribution": states_count
        }
        
        logger.info(f"📊 Статистика сессий: {stats}")
        return stats


# Глобальный экземпляр для использования в приложении
dialog_manager = DialogStateManager() 