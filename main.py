import os
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# Получаем токен из переменной окружения (так он безопаснее хранится на сервере)
TELEGRAM_TOKEN = os.getenv("TOKEN")

# Директория для временного хранения загруженных аудио файлов (Railway допускает временную директорию /tmp)
output_path = '/tmp'

# Функция для загрузки аудио с YouTube и конвертации в MP3
def download_audio(youtube_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            audio_file_path = os.path.join(output_path, f"{info['title']}.mp3")
            return audio_file_path
    except Exception as e:
        print(f"Произошла ошибка при загрузке: {e}")
        return None

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Отправьте мне ссылку на YouTube видео, и я скачаю аудио в формате MP3.")

# Функция для обработки сообщений с ссылкой
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    youtube_url = update.message.text
    await update.message.reply_text("Загружаю аудио, подождите несколько секунд...")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT)

    # Загружаем и конвертируем аудио
    audio_file_path = download_audio(youtube_url)
    if audio_file_path:
        # Отправляем пользователю аудио файл
        await update.message.reply_audio(audio=open(audio_file_path, 'rb'))
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
