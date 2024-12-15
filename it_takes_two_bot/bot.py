import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import os
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import environ

env = environ.Env()
logger = logging.getLogger(__name__)

API_TOKEN = env("TELEGRAM_API_TOKEN")


def start(update: Update, context):
    update.message.reply_text("Send an audio file, and type /broadcast to play it!")


def handle_audio(update: Update, context):
    if update.message.audio:
        audio = update.message.audio
        file_id = audio.file_id

        audio_file = update.message.bot.get_file(file_id)
        audio_file.download(f"downloads/{audio.file_id}.mp3")

        update.message.reply_text("Got your music! Use /broadcast to play it.")


def get_file_from_s3(file_name: str):
    try:
        config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
        session = boto3.Session()
        s3 = session.client("s3", config=config, region_name=env("REGION"))
        response = s3.get_object(Bucket=env("BUCKET_NAME"), Key=file_name)
        file = response["Body"]
    except ClientError as e:
        logger.error(f"S3 ClientError: {str(e)}")
        raise
    return file


def broadcast(update: Update, context):
    try:
        song_name = '_'.join(context.args).lower()
        file = get_file_from_s3(song_name)
        response = requests.get(file, stream=True)
        if response.status_code == 200:
            with open("broadcast_audio.mp3", "wb") as audio_file:
                audio_file.write(response.content)

            update.message.reply_text("Playing your music...")
            context.bot.send_audio(update.message.chat_id, open("broadcast_audio.mp3", 'rb'))

            os.remove("broadcast_audio.mp3")
        else:
            update.message.reply_text("Failed to fetch the audio file. Please try again later.")
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")


def handle_text(update: Update, context):
    update.message.reply_text("Send me an audio file to share and type /broadcast to play it.")


if __name__ == '__main__':
    try:
        updater = Updater(API_TOKEN, use_context=True)

        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("broadcast", broadcast))
        dispatcher.add_handler(MessageHandler(Filters.audio, handle_audio))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

        updater.start_polling()
        updater.idle()
    except Exception as e:
        logger.error(f"Telegram Bot Error: {str(e)}")
