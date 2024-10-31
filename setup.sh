#!/bin/bash
apt-get update
apt-get install -y ffmpeg
ffmpeg -version  # Проверка установленной версии ffmpeg
echo "Путь к ffmpeg: $FFMPEG_PATH"  # Выводим путь в логах