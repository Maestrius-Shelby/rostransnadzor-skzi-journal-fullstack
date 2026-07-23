#!/bin/bash
# setup_chromedriver.sh - Установка ChromeDriver для Linux

echo "📥 Установка ChromeDriver для Linux..."

# Создаем папку
mkdir -p linux/chromedriver-linux64

# Скачиваем
cd linux
wget https://storage.googleapis.com/chrome-for-testing-public/latest/linux64/chromedriver-linux64.zip

# Распаковываем
unzip chromedriver-linux64.zip

# Делаем исполняемым
chmod +x chromedriver-linux64/chromedriver

# Удаляем архив
rm chromedriver-linux64.zip

echo "✅ ChromeDriver установлен!"
echo "Путь: $(pwd)/chromedriver-linux64/chromedriver"