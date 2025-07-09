# Makefile для help_bot_ai

.PHONY: help install build up down logs restart status clean

# Показать доступные команды
help:
	@echo "🤖 Help Bot AI - Команды управления"
	@echo ""
	@echo "📦 Установка и сборка:"
	@echo "  make install     - Установка зависимостей через uv"
	@echo "  make build       - Сборка Docker образа"
	@echo ""
	@echo "🚀 Запуск и управление:"
	@echo "  make up          - Запуск приложения (docker-compose up -d)"
	@echo "  make down        - Остановка приложения"
	@echo "  make restart     - Перезапуск приложения"
	@echo ""
	@echo "📊 Мониторинг:"
	@echo "  make logs        - Просмотр логов"
	@echo "  make status      - Статус контейнеров"
	@echo ""
	@echo "🧹 Обслуживание:"
	@echo "  make clean       - Очистка Docker образов и контейнеров"

# Установка зависимостей через uv
install:
	@echo "📦 Установка зависимостей..."
	uv sync

# Сборка Docker образа
build:
	@echo "🐳 Сборка Docker образа..."
	docker-compose build

# Запуск приложения
up:
	@echo "🚀 Запуск help_bot_ai..."
	docker-compose up -d
	@echo "✅ Приложение запущено!"
	@echo "📊 Проверьте статус: make status"
	@echo "📝 Просмотр логов: make logs"

# Остановка приложения
down:
	@echo "🛑 Остановка help_bot_ai..."
	docker-compose down

# Перезапуск приложения
restart:
	@echo "🔄 Перезапуск help_bot_ai..."
	docker-compose restart
	@echo "✅ Приложение перезапущено!"

# Просмотр логов
logs:
	@echo "📝 Логи help_bot_ai:"
	docker-compose logs -f

# Статус контейнеров
status:
	@echo "📊 Статус контейнеров:"
	docker-compose ps
	@echo ""
	@echo "💾 Использование ресурсов:"
	docker stats --no-stream

# Очистка
clean:
	@echo "🧹 Очистка Docker..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Очистка завершена!"

# Обновление из git
update:
	@echo "📥 Обновление из Git..."
	git pull origin main
	@echo "🐳 Пересборка образа..."
	docker-compose build
	@echo "🔄 Перезапуск..."
	docker-compose up -d
	@echo "✅ Обновление завершено!"

# Проверка конфигурации
check:
	@echo "🔍 Проверка конфигурации:"
	@echo "📁 Структура проекта:"
	ls -la
	@echo ""
	@echo "⚙️ Файл .env:"
	@if [ -f .env ]; then echo "✅ .env найден"; else echo "❌ .env не найден! Скопируйте из .env.example"; fi
	@echo ""
	@echo "🐳 Docker статус:"
	docker --version
	docker-compose --version 