import json
import os
from typing import List, Dict, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from src.config.settings import logger


class KnowledgeSearcher:
    """
    Поиск по базе знаний услуг компании
    Использует ChromaDB для векторного поиска и sentence-transformers для эмбеддингов
    """
    
    def __init__(self, services_file: str = "doc/services_knowledge_base.json"):
        """
        Инициализация поисковика
        
        Args:
            services_file: Путь к файлу с услугами
        """
        logger.info("🔍 Инициализация системы поиска по базе знаний")
        
        # Инициализация модели для векторизации (локальная)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Модель sentence-transformers загружена")
        
        # Инициализация ChromaDB (файловая БД)
        os.makedirs("data/chroma", exist_ok=True)
        self.client = chromadb.PersistentClient(path="data/chroma")
        self.collection = self.client.get_or_create_collection(
            name="services",
            metadata={"description": "Услуги Академии дронов"}
        )
        logger.info("✅ ChromaDB инициализирована")
        
        # Загрузка услуг в БД
        self.services_file = services_file
        self._load_services_if_needed()
        
        logger.info(f"🎯 Система поиска готова. Услуг в БД: {self.collection.count()}")

    def _load_services_if_needed(self):
        """Загружает услуги в БД если она пустая"""
        if self.collection.count() == 0:
            logger.info("📦 База данных пустая, загружаем услуги")
            self.load_services_from_file()
        else:
            logger.info(f"📊 База данных уже содержит {self.collection.count()} услуг")

    def load_services_from_file(self):
        """
        Загружает услуги из JSON файла в векторную БД
        """
        try:
            with open(self.services_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            services = data.get('services', [])
            logger.info(f"📋 Загружаем {len(services)} услуг в векторную БД")
            
            # Подготовка данных для ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for service in services:
                # Создаем полный текст для векторизации
                search_text = self._create_search_text(service)
                documents.append(search_text)
                
                # Метаданные для фильтрации и возврата результатов
                metadata = {
                    "id": service["id"],
                    "name": service["name"],
                    "category": service["category"],
                    "courseCode": service.get("courseCode", ""),
                    "price": self._extract_price(service),
                }
                metadatas.append(metadata)
                ids.append(service["id"])
            
            # Добавление в ChromaDB (автоматическая векторизация)
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ Загружено {len(services)} услуг в векторную БД")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки услуг: {e}")
            raise

    def _create_search_text(self, service: Dict) -> str:
        """
        Создает полный текст для векторизации из данных услуги
        
        Args:
            service: Данные услуги
            
        Returns:
            Объединенный текст для поиска
        """
        text_parts = [
            service["name"],
            service["category"],
            service.get("sub_category", ""),
            service.get("full_description", "")
        ]
        
        # Добавляем детали услуги
        details = service.get("details", {})
        if isinstance(details, dict):
            for key, value in details.items():
                if isinstance(value, str):
                    text_parts.append(f"{key}: {value}")
                elif isinstance(value, list):
                    text_parts.extend(value)
        
        # Объединяем в один текст
        return " ".join(filter(None, text_parts))

    def _extract_price(self, service: Dict) -> str:
        """Извлекает цену из данных услуги"""
        details = service.get("details", {})
        if isinstance(details, dict):
            return details.get("Цена", "Не указана")
        return "Не указана"

    def search(self, query: str, limit: int = 3) -> List[Dict]:
        """
        Поиск релевантных услуг по запросу
        
        Args:
            query: Поисковый запрос пользователя
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных услуг с метаданными
        """
        try:
            logger.info(f"🔍 Поиск по запросу: '{query}' (лимит: {limit})")
            
            # Выполняем векторный поиск
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                include=["metadatas", "documents", "distances"]
            )
            
            # Формируем ответ
            found_services = []
            if results['metadatas'] and results['metadatas'][0]:
                for i, metadata in enumerate(results['metadatas'][0]):
                    distance = results['distances'][0][i]
                    similarity = 1 - distance  # Преобразуем расстояние в схожесть
                    
                    service_result = {
                        "id": metadata["id"],
                        "name": metadata["name"],
                        "category": metadata["category"],
                        "courseCode": metadata["courseCode"],
                        "price": metadata["price"],
                        "similarity": round(similarity, 3),
                        "relevance_score": round(similarity * 100, 1)
                    }
                    found_services.append(service_result)
            
            logger.info(f"✅ Найдено {len(found_services)} релевантных услуг")
            for service in found_services:
                logger.info(f"  📌 {service['name']} (релевантность: {service['relevance_score']}%)")
                
            return found_services
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return []

    def get_service_details(self, service_id: str) -> Optional[Dict]:
        """
        Получает полные детали услуги по ID
        
        Args:
            service_id: Идентификатор услуги
            
        Returns:
            Полная информация об услуге или None
        """
        try:
            with open(self.services_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            services = data.get('services', [])
            for service in services:
                if service["id"] == service_id:
                    logger.info(f"📄 Получены детали услуги: {service['name']}")
                    return service
                    
            logger.warning(f"⚠️ Услуга с ID '{service_id}' не найдена")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения деталей услуги: {e}")
            return None

    def search_and_format_for_telegram(self, query: str, limit: int = 3) -> str:
        """
        Поиск услуг с форматированием для отправки в Telegram
        
        Args:
            query: Поисковый запрос пользователя
            limit: Максимальное количество результатов
            
        Returns:
            Отформатированный текст для отправки пользователю
        """
        results = self.search(query, limit)
        
        if not results:
            return (
                "🤔 К сожалению, я не нашел подходящих услуг по вашему запросу.\n\n"
                "Попробуйте переформулировать или напишите мне более конкретно, "
                "что вас интересует (например: 'обучение полетам', 'корпоративные мероприятия', 'индивидуальные занятия')."
            )
        
        response = f"🎯 Нашел для вас {len(results)} подходящих услуг:\n\n"
        
        for i, service in enumerate(results, 1):
            response += f"**{i}. {service['name']}**\n"
            response += f"📂 Категория: {service['category']}\n"
            response += f"💰 Цена: {service['price']}\n"
            
            # Добавляем детальную информацию если доступна
            details = self.get_service_details(service['id'])
            if details and details.get('details'):
                service_details = details['details']
                if isinstance(service_details, dict):
                    # Показываем ключевые детали
                    key_info = []
                    for key, value in service_details.items():
                        if key not in ['Цена'] and isinstance(value, str):
                            key_info.append(f"{key}: {value}")
                    
                    if key_info:
                        response += f"ℹ️ {', '.join(key_info[:2])}\n"  # Максимум 2 детали
            
            response += f"🏷️ Код: {service['courseCode']}\n\n"
        
        response += "💬 Хотите узнать подробнее о какой-то из услуг или у вас есть другие вопросы?"
        
        return response

    def format_service_details(self, service_id: str) -> str:
        """
        Форматирует полную информацию об услуге для Telegram
        
        Args:
            service_id: Идентификатор услуги
            
        Returns:
            Подробная информация об услуге
        """
        service = self.get_service_details(service_id)
        
        if not service:
            return "❌ Услуга не найдена. Попробуйте поискать еще раз."
        
        response = f"📋 **{service['name']}**\n\n"
        response += f"📂 Категория: {service['category']}\n"
        
        if service.get('sub_category'):
            response += f"📁 Подкатегория: {service['sub_category']}\n"
        
        # Детали услуги
        details = service.get('details', {})
        if isinstance(details, dict):
            response += "\n💡 **Детали:**\n"
            for key, value in details.items():
                if isinstance(value, str):
                    response += f"• {key}: {value}\n"
                elif isinstance(value, list):
                    response += f"• {key}:\n"
                    for item in value:
                        response += f"  - {item}\n"
        
        # Полное описание
        if service.get('full_description'):
            response += f"\n📖 **Описание:**\n{service['full_description']}\n"
        
        response += f"\n🏷️ Код услуги: {service.get('courseCode', 'Не указан')}"
        
        return response


# Глобальный экземпляр для использования в приложении
knowledge_searcher = KnowledgeSearcher()

# Удобные функции для использования в handlers
def search_services(query: str, limit: int = 3) -> str:
    """Поиск услуг с форматированием для Telegram"""
    return knowledge_searcher.search_and_format_for_telegram(query, limit)

def get_service_info(service_id: str) -> str:
    """Получение подробной информации об услуге"""
    return knowledge_searcher.format_service_details(service_id) 