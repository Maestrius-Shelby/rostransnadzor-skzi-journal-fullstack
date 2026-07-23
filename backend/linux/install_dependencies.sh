#!/bin/bash
# install_dependencies.sh - Установка зависимостей для altLinux

echo "=========================================="
echo "📦 Установка зависимостей для altLinux"
echo "=========================================="

# Обновление пакетов
echo "➜ Обновление пакетов..."
sudo apt-get update

# Установка Chromium
echo "➜ Установка Chromium..."
sudo apt-get install -y chromium-browser || sudo apt-get install -y chromium

# Установка Python и pip
echo "➜ Установка Python..."
sudo apt-get install -y python3 python3-pip python3-venv

# Установка X11 утилит
echo "➜ Установка X11 утилит..."
sudo apt-get install -y x11-utils xdotool

# Установка зависимостей для OpenCV
echo "➜ Установка OpenCV зависимостей..."
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0

# Создание виртуального окружения
echo "➜ Создание виртуального окружения..."
python3 -m venv venv

# Активация и установка пакетов
echo "➜ Установка Python пакетов..."
source venv/bin/activate
pip install -r requirements.txt

echo "=========================================="
echo "✅ Готово!"
echo "=========================================="
echo "Для запуска:"
echo "  source venv/bin/activate"
echo "  python main_linux.py"