# 🚀 Развертывание help_bot_ai на VPS

## 📋 Информация о сервере

- **IP:** 45.146.166.172
- **Пользователь:** root
- **ОС:** Ubuntu 24.04
- **Пароль:** yEoJ6!fU3!eR

## 🛠 Пошаговое развертывание

### Шаг 1: Подключение к серверу

```bash
ssh root@45.146.166.172
# Введите пароль: yEoJ6!fU3!eR
```

### Шаг 2: Выполнение скрипта установки

```bash
# Скачиваем скрипт установки
curl -sSL https://raw.githubusercontent.com/osipovia/help_bot_ai/main/deploy_setup.sh > setup.sh
chmod +x setup.sh
./setup.sh
```

**ИЛИ ручная установка:**

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Клонирование проекта
cd /opt
git clone https://github.com/osipovia/help_bot_ai.git
cd help_bot_ai
```

### Шаг 3: Настройка переменных окружения

```bash
cd /opt/help_bot_ai
cp .env.example .env
nano .env
```

**Необходимые настройки в .env:**

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=ваш_токен_бота

# OpenRouter API  
OPENROUTER_API_KEY=ваш_ключ_openrouter

# 1C Integration
ONEC_API_URL=https://api.example.com/1c-integration
ONEC_CLIENT_ID=whatsapp_bot_prod_001
ONEC_CLIENT_SECRET=ваш_секретный_ключ

# Application Settings
LOG_LEVEL=INFO
```

### Шаг 4: Запуск приложения

```bash
# Сборка и запуск
make build
make up

# ИЛИ напрямую через docker-compose
docker-compose up -d --build
```

### Шаг 5: Проверка работы

```bash
# Проверка статуса
make status

# Просмотр логов
make logs

# Проверка ресурсов
htop
```

## 🔧 Управление приложением

### Полезные команды

```bash
# Просмотр доступных команд
make help

# Перезапуск приложения
make restart

# Остановка приложения  
make down

# Обновление из Git
make update

# Просмотр логов в реальном времени
make logs

# Очистка системы
make clean
```

### Мониторинг

```bash
# Статус контейнеров
docker ps

# Использование ресурсов
docker stats

# Логи приложения
docker-compose logs -f help_bot_ai

# Системные ресурсы
htop
df -h
```

## 🔐 Безопасность

### Настройка файрвола

```bash
# Установка ufw
apt install ufw

# Разрешить SSH
ufw allow 22

# Разрешить HTTP/HTTPS (если нужно)
ufw allow 80
ufw allow 443

# Включить файрвол
ufw enable
```

### Автоматическое обновление

```bash
# Создание cron задачи для обновления
crontab -e

# Добавить строку (проверка обновлений каждый день в 3:00)
0 3 * * * cd /opt/help_bot_ai && git pull && docker-compose up -d --build
```

## 📊 Мониторинг ресурсов

### Проверка памяти и CPU

```bash
# Текущее использование
free -h
top
htop

# Использование диска
df -h
du -sh /opt/help_bot_ai/

# Сетевые подключения
netstat -tulpn | grep docker
```

### Логи системы

```bash
# Системные логи
journalctl -u docker
systemctl status docker

# Логи приложения
tail -f /opt/help_bot_ai/logs/app.log
```

## 🚨 Устранение неполадок

### Проблемы с запуском

```bash
# Проверка Docker
systemctl status docker
docker info

# Перезапуск Docker
systemctl restart docker

# Проверка портов
netstat -tulpn | grep :8000
```

### Проблемы с памятью

```bash
# Очистка Docker
docker system prune -a

# Очистка логов
truncate -s 0 /var/log/docker.log

# Добавление swap (если нужно)
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

## 📞 Контакты и поддержка

- **GitHub:** https://github.com/osipovia/help_bot_ai
- **Документация:** См. файлы в папке `doc/`

## 🎯 Следующие шаги

1. ✅ Настроить мониторинг
2. ✅ Настроить автоматические бэкапы
3. ✅ Настроить SSL сертификаты (если нужен веб-интерфейс)
4. ✅ Настроить логирование в внешнюю систему 