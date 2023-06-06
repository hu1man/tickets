import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import io
import requests
import logging
import telegram
import telebot
import googleapiclient
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Telegram Bot Token
TELEGRAM_TOKEN = '6282061926:AAE1Ztj78CZpnR4pzlKRnLwTI1ZDsIEByu0'

# Google Sheets credentials
GOOGLE_SHEETS_CREDS_FILE = 'credentials.json'
GOOGLE_SHEETS_SPREADSHEET = 'tickets'

# Google Sheets table headings
TABLE_HEADINGS = ['NAME', 'T.NO']

# Google Drive Credentials
GOOGLE_DRIVE_CREDENTIALS = 'credentials1.json'
GOOGLE_DRIVE_FOLDER_ID = '1IsECU6-DxSOLw8wj-ErhFN8ElixgL-6q'

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Telegram Bot instance
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Google Drive API credentials
drive_credentials = service_account.Credentials.from_service_account_file(
    GOOGLE_DRIVE_CREDENTIALS,
    scopes=['https://www.googleapis.com/auth/drive']
)

# Google Drive API service
drive_service = build('drive', 'v3', credentials=drive_credentials)


def start(update, context):
    """Handler for /start command."""
    chat_id = update.message.chat_id
    bot.send_photo(chat_id, 'https://imgur.com/3Rmd6Ji', caption=f"""🇺🇦 OBSCURA ‘23 බොට් හදලා තියෙන්නේ ඔයාලට Online Tickets Book කරගන්න පහසු වෙන්න.මේකෙන් ඔයාලට ඔයාලගේ Online Tickets ලේසියෙන් Book කරගන්න පුලුවන්. 🇺🇦
ඔයාලට කරන්න තියෙන්නේ මෙච්චරයි… 

1.ඔයාලගේ නම දෙන්න.
2.ඊටපස්සේ ඔයාලගේ Whatsapp අංකය දෙන්න
3.ටිකකින් බොට් මැසේජ් කරලා ඔයාලගෙන් මුදල් ගෙවපු Slip එකේ Photo එකක් ඉල්ලයි. ඔයාලා මුදල් ගෙවපු Slip එකේ ඔයාලගේ නම ලියලා Photo එකක් බොට් ට Send කරන්න.
4.සංවිධායක මණ්ඩලේ අය ඊටපස්සේ ඔයාලව Whatsapp වලින් සම්බන්ධ කරගනී.

🤨 මොනාහරි ප්‍රශ්න තියනවනම් , 🤨

🎆 Janidu - 0701987535
🎆 Gayashan -  0714332070 මෙයාලව Contact කරගන්න.

bot by - @drkvidun""")

    welcome_message = "ඔයාගේ නම ඇතුලත් කරන්න"
    context.bot.send_message(chat_id=chat_id, text=welcome_message)
    
    # Reset user data
    context.user_data.clear()


def receive_message(update, context):
    """Handler for receiving messages."""
    chat_id = update.message.chat_id
    user_input = update.message.text

    # Check the current state of the conversation
    if 'name' not in context.user_data:
        # Save the user's name
        context.user_data['name'] = user_input
        phone_number_message = "Thank you…! ඔයාගේ Whatsapp Number එක ඇතුලත් කරන්න"
        context.bot.send_message(chat_id=chat_id, text=phone_number_message)
    elif 'phone_number' not in context.user_data:
        # Save the user's phone number
        context.user_data['phone_number'] = user_input
        save_data_to_google_sheets(context.user_data)
        confirmation_message = "Thank you! Your data has been saved. මුදල් ගෙවපු Slip එකේ ඔයාගේ නම සඳහන් කරලා Send කරන්න."
        context.bot.send_message(chat_id=chat_id, text=confirmation_message)


def save_data_to_google_sheets(user_data):
    """Save user data to Google Sheets."""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDS_FILE, scope)
    client = gspread.authorize(creds)

    sheet = client.open(GOOGLE_SHEETS_SPREADSHEET).sheet1

    row = [user_data.get('name'), user_data.get('phone_number')]
    sheet.append_row(row)


def save_image_to_google_drive(file_id):
    """Upload the image to Google Drive."""
    try:
        # Get the file from Telegram
        file = bot.get_file(file_id)

        # Download the image file
        image_url = file.file_path
        response = requests.get(image_url)
        image_data = response.content

        # Upload the image to Google Drive
        file_metadata = {
            'name': file_id + '.jpg',  # Use a unique name for each file
            'parents': [GOOGLE_DRIVE_FOLDER_ID]
        }
        media = googleapiclient.http.MediaIoBaseUpload(io.BytesIO(image_data), mimetype='image/jpeg')
        drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return True
    except Exception as e:
        logging.error(str(e))
        return False


def handle_image(update, context):
    """Handler for receiving image messages."""
    chat_id = update.effective_chat.id
    if update.message.photo:
        # Get the largest photo sent by the user
        file_id = update.message.photo[-1].file_id

        # Save the image to Google Drive
        if save_image_to_google_drive(file_id):
            context.bot.send_message(chat_id=chat_id, text="Image uploaded successfully!")
        else:
            context.bot.send_message(chat_id=chat_id, text="Failed to upload the image.")
    else:
        context.bot.send_message(chat_id=chat_id, text="Please send an image.")


def main():
    """Start the bot."""
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, receive_message))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_image))

    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
