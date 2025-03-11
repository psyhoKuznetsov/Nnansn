import telebot
import aiohttp
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import os
import logging
bot = telebot.TeleBot('7451126954:AAGJZFNx8GhIwWFwpYrM8bc7dyOs0TaGwaw')

def get_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Проверить один ключ"))
    keyboard.add(KeyboardButton("Проверить несколько ключей"))
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я бот для проверки API ключей.\nВыберите режим проверки:",
        reply_markup=get_keyboard()
    )

user_states = {}

async def check_api(api_key: str):
    TEXT_API_URL = "http://aeza.theksenon.pro/v1/api/text/generate"
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "prompt": "привет"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(TEXT_API_URL, headers=headers, json=data) as response:
                if response.status == 200:
                    return f"{api_key}  ✅"
                else:
                    return f"{api_key}  ❌"
        except Exception as e:
            return f"{api_key}  ❌"

@bot.message_handler(func=lambda message: message.text == "Проверить один ключ")
def check_single(message):
    user_states[message.chat.id] = "single"
    bot.send_message(message.chat.id, "Отправьте API ключ для проверки:")

@bot.message_handler(func=lambda message: message.text == "Проверить несколько ключей")
def check_multiple(message):
    user_states[message.chat.id] = "multiple"
    bot.send_message(message.chat.id, "Отправьте список API ключей (каждый с новой строки):")

@bot.message_handler(func=lambda message: True)
def handle_keys(message):
    if message.chat.id not in user_states:
        start(message)
        return

    state = user_states[message.chat.id]
    
    if state == "single":
        if not message.text.startswith("ksenon-"):
            bot.reply_to(message, "Некорректный API ключ. Убедитесь, что он начинается с 'ksenon-'")
            return
        
        async def check():
            result = await check_api(message.text.strip())
            bot.reply_to(message, result)
        
        asyncio.run(check())
        user_states[message.chat.id] = None
        
    elif state == "multiple":
        keys = [key.strip() for key in message.text.split('\n') if key.strip().startswith("ksenon-")]
        if not keys:
            bot.reply_to(message, "Не найдено корректных API ключей")
            return
            
        async def check_all():
            tasks = [check_api(key) for key in keys]
            results = await asyncio.gather(*tasks)
            response = "\n".join(results)
            bot.reply_to(message, response)
        
        asyncio.run(check_all())
        user_states[message.chat.id] = None

def main():
    while True:
        try:
            print("Бот запущен...")
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            logging.error(f"🔴 Произошла ошибка: {e}")
            print(f"🔴 Ошибка: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
