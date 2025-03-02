import os
import telebot
import google.generativeai as genai
import speechrecognition as sr
import requests
from dotenv import load_dotenv
from telebot import types
from PIL import Image
from datetime import datetime, timedelta
from pydub import AudioSegment  # For format conversion

# ✅ Load environment variables
load_dotenv()

# ✅ Securely fetch API keys from .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot('7466064529:AAEZXDgQb27yxa_24G_eVR25u9qkLyl8bXU')

# ✅ Verify API keys are loaded
if not GEMINI_API_KEY or not TOKEN:
    print("❌ ERROR: Missing API keys. Check your .env file!")
    exit()

# ✅ Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Initialize Telegram bot
bot = telebot.TeleBot(TOKEN)

# ✅ Store user conversations for context
user_memory = {}
session_timeout = {}

# ✅ Time limit for session (300 minutes inactivity)
SESSION_LIMIT = timedelta(minutes=300)

# ✅ Start command
@bot.message_handler(commands=['start'])
def welcome_message(message):
    bot.send_message(message.chat.id, "🚀 Welcome to 𝓒𝓱𝓪𝓽𝓝𝓸𝓿𝓪! Type anything to start chatting.")

    # ✅ Send logo (Ensure "chatnova_logo.png" is in the same folder)
    try:
        with open("chatnova_logo.png", "rb") as logo:
            bot.send_photo(message.chat.id, logo)
    except FileNotFoundError:
        bot.send_message(message.chat.id, "⚠️ Logo not found! Please check the file path.")

# ✅ Help command
@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, "💡 **Available Commands:**\n"
                                      "/start - Start the bot\n"
                                      "/reset - Clear memory\n"
                                      "/image - Generate AI images\n"
                                      "/translate - Translate text\n"
                                      "/search - Google Search\n"
                                      "/file - Analyze documents\n"
                                      "/voice - Send voice messages\n"
                                      "/code - Run Python code")

# ✅ Reset command
@bot.message_handler(commands=['reset'])
def reset_memory(message):
    user_memory.pop(message.chat.id, None)
    session_timeout.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "🔄 Memory cleared! Let's start fresh.")

# ✅ Image Analysis Handler
@bot.message_handler(content_types=['photo'])
def image_analysis(message):
    bot.send_message(message.chat.id, "📸 **Processing your image...**")

    # ✅ Get file info & download image
    file_info = bot.get_file(message.photo[-1].file_id)
    file_path = file_info.file_path
    downloaded_file = bot.download_file(file_path)

    # ✅ Save image temporarily
    image_path = "user_image.jpg"
    with open(image_path, 'wb') as img_file:
        img_file.write(downloaded_file)

    try:
        # ✅ Open and encode image
        with open(image_path, "rb") as image_file:
            image_blob = {
                "mime_type": "image/jpeg",  # Adjust if using PNG
                "data": image_file.read()
            }

        # ✅ Initialize Gemini Model
        model = genai.GenerativeModel("gemini-1.5-flash")

        # ✅ Prepare request with text prompt + image
        response = model.generate_content(
            contents=[{"parts": [{"inline_data": image_blob}]}]
        )

        # ✅ Extract AI-generated response
        bot_response = response.text if response.text else "⚠️ No description available."

    except Exception as e:
        bot_response = f"⚠️ Error: {str(e)}"

    bot.send_message(message.chat.id, bot_response)

# ✅ AI Image Generation
@bot.message_handler(commands=['image'])
def generate_ai_image(message):
    prompt = message.text.replace("/image", "").strip()
    if not prompt:
        bot.send_message(message.chat.id, "🎨 **Please provide an image prompt!** Example: `/image futuristic city at night`")
        return
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        bot.send_message(message.chat.id, f"🖼 **AI-Generated Image:** {response.text}")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {str(e)}")

# ✅ Google Search Integration
@bot.message_handler(commands=['search'])
def google_search(message):
    query = message.text.replace("/search", "").strip()
    if not query:
        bot.send_message(message.chat.id, "🔍 **Please enter a search query!** Example: `/search latest AI trends`")
        return
    
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key=YOUR_GOOGLE_API_KEY&cx=YOUR_SEARCH_ENGINE_ID"
    
    try:
        response = requests.get(url).json()
        if "items" in response:
            results = "\n".join([f"🔹 {item['title']}: {item['link']}" for item in response["items"][:3]])
            bot.send_message(message.chat.id, f"🔍 **Top Search Results:**\n{results}")
        else:
            bot.send_message(message.chat.id, "⚠️ No results found.")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {str(e)}")

# ✅ Voice Message Processing
@bot.message_handler(content_types=['voice'])
def voice_to_text(message):
    bot.send_message(message.chat.id, "🎤 **Processing your voice message...**")
    
    file_info = bot.get_file(message.voice.file_id)
    file_path = file_info.file_path
    downloaded_file = bot.download_file(file_path)
    
    oga_path = "voice.ogg"
    with open(oga_path, 'wb') as audio_file:
        audio_file.write(downloaded_file)
    
    wav_path = "voice.wav"
    audio = AudioSegment.from_file(oga_path, format="ogg")
    audio.export(wav_path, format="wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            bot.send_message(message.chat.id, f"🗣 **Transcribed Text:** {text}")
        except sr.UnknownValueError:
            bot.send_message(message.chat.id, "❌ Could not understand the audio.")
        except sr.RequestError:
            bot.send_message(message.chat.id, "❌ Speech recognition service error.")

@bot.message_handler(content_types=['voice'])
def voice_to_text(message):
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # Save the received OGG file
    oga_path = "voice.ogg"
    with open(oga_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    # Convert OGG to WAV
    wav_path = "voice.wav"
    audio = AudioSegment.from_file(oga_path, format="ogg")
    audio.export(wav_path, format="wav")

    # Process the WAV file with speech recognition
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            bot.reply_to(message, f"🎙 Transcribed: {text}")
        except sr.UnknownValueError:
            bot.reply_to(message, "❌ Could not understand the audio.")
        except sr.RequestError:
            bot.reply_to(message, "❌ Speech recognition service error.")
    
bot.polling()

# ✅ AI Response Handler
@bot.message_handler(func=lambda message: True)
def chatbot_response(message):
    user_id = message.chat.id
    user_message = message.text

     # ✅ Check if session expired
    if user_id in session_timeout and datetime.now() - session_timeout[user_id] > SESSION_LIMIT:
        user_memory.pop(user_id, None)

    # ✅ Store conversation history (limit to last 5 messages)
    user_memory.setdefault(user_id, []).append(user_message)
    user_memory[user_id] = user_memory[user_id][-10:]
    session_timeout[user_id] = datetime.now()

    model = genai.GenerativeModel("gemini-1.5-flash")
    try:
        context = " ".join(user_memory[user_id])
        response = model.generate_content(context)
        bot_response = response.text if response.text else "⚠️ I couldn't generate a response."
    except Exception as e:
        bot_response = f"⚠️ Error: {str(e)}"

    bot.send_message(user_id, bot_response)

print("🤖 ChatNova is running...")
bot.polling(none_stop=True, interval=0)
