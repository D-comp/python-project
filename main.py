import os
import logging
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
import re

# Инициализируем логирование
#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

# Получаем токен из переменной окружения
TELEGRAM_TOKEN = os.getenv("TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("Необходимо установить токен Telegram в переменной окружения 'TOKEN'.")

# Директория для временного хранения загруженных аудио файлов
output_path = '/tmp'

# Функция для предотвращения ошибки нечитаемых символов в названии ролика
def sanitize_filename(filename):
    return re.sub(r'[\\/:"*?<>|]+', '', filename)

# Функция для выбора качества аудио в зависимости от длительности ролика
def get_quality_by_duration(duration):
    if duration < 600:  # меньше 10 минут
        return '192'
    elif duration < 1800:  # меньше 30 минут
        return '128'
    else:  # более 30 минут
        return '96'

# Функция для загрузки аудио с YouTube и конвертации в MP3
def download_audio(youtube_url):
    try:
        # Получаем информацию о видео для определения длительности
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            duration = info.get('duration', 0)
            quality = get_quality_by_duration(duration)
            sanitized_title = sanitize_filename(info['title'])

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, f'{sanitized_title}.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
            audio_file_path = os.path.join(output_path, f"{sanitized_title}.mp3")
            return audio_file_path
    except Exception as e:
        logger.error(f"Произошла ошибка при загрузке: {e}")
        return None

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Отправьте мне ссылку на YouTube видео, и я скачаю аудио в формате MP3.")

# Функция для обработки сообщений с ссылкой
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    youtube_url = update.message.text

    # Проверка на валидность ссылки
    if not re.match(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+', youtube_url):
        await update.message.reply_text("Пожалуйста, отправьте корректную ссылку на YouTube видео.")
        return

    await update.message.reply_text("Загружаю аудио, подождите несколько секунд...")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT)

    # Загружаем и конвертируем аудио
    audio_file_path = download_audio(youtube_url)
    if audio_file_path:
        try:
            await update.message.reply_audio(audio=open(audio_file_path, 'rb'))
        except Exception as e:
            logger.error(f"Ошибка при отправке файла: {e}")
            await update.message.reply_text("Произошла ошибка при отправке аудио.")
        finally:
            os.remove(audio_file_path)  # Удаляем файл после отправки
    else:
        await update.message.reply_text("Произошла ошибка при загрузке аудио.")

# Основная функция для запуска бота
def main():
    # Создаем приложение бота
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
