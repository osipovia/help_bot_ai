#!/bin/bash

# Скрипт установки help_bot_ai на Ubuntu 24.04 VPS
# IP: 45.146.166.172

echo "🚀 Начинаем установку help_bot_ai на VPS..."

# Обновление системы
echo "📦 Обновление системы..."
apt update && apt upgrade -y

# Установка базовых пакетов
echo "📦 Установка базовых пакетов..."
apt install -y \
    curl \
    wget \
    git \
    htop \
    nano \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Установка Docker
echo "🐳 Установка Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Запуск Docker
systemctl start docker
systemctl enable docker

# Установка Python 3.11+
echo "🐍 Установка Python 3.11..."
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Создание пользователя для приложения (опционально)
echo "👤 Создание пользователя helpbot..."
useradd -m -s /bin/bash helpbot
usermod -aG docker helpbot

# Установка uv (современный менеджер пакетов Python)
echo "📦 Установка uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Клонирование проекта
echo "📥 Клонирование проекта..."
cd /opt
git clone https://github.com/osipovia/help_bot_ai.git
cd help_bot_ai

# Настройка прав доступа
chown -R helpbot:helpbot /opt/help_bot_ai

echo "✅ Базовая установка завершена!"
echo "📋 Следующие шаги:"
echo "1. Настройте .env файл с вашими API ключами"
echo "2. Запустите: docker-compose up -d --build"
echo "3. Проверьте логи: docker-compose logs -f"

# Создание .env файла из примера
echo "⚙️ Создание .env файла..."
cp .env.example .env

echo "🎯 Отредактируйте .env файл:"
echo "nano .env"

# Показать содержимое .env.example для справки
echo "📝 Шаблон .env файла:"
cat .env.example 