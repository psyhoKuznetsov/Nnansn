import json
import os
import time
import telebot
from telebot import types
import logging
import random
import string
from datetime import datetime, timedelta

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "7388296079:AAGkl4cdsnZ1QYe3xjjTNh2uGEghGLkA4tQ" 
ADMIN_IDS = [7134890858] 
WELCOME_PHOTO = "https://files.catbox.moe/1t54da.jpg"
DEFAULT_AVATAR = "https://files.catbox.moe/dgi1qw.mp4"
USD_RATE = 89.1362
KEY_IMAGES = {
    "1_day": "https://files.catbox.moe/67u8ed.jpg",
    "3_days": "https://files.catbox.moe/wbh5x0.jpg",
    "7_days": "https://files.catbox.moe/79cb1u.jpg",
    "14_days": "https://files.catbox.moe/rnjgzv.jpg",
    "30_days": "https://files.catbox.moe/kom0fm.jpg",
    "60_days": "https://files.catbox.moe/oq3umz.jpg"
}

PRICES = {
    "1_day": {"rub": 60, "usd": 0.67},
    "3_days": {"rub": 150, "usd": 1.68},
    "7_days": {"rub": 250, "usd": 2.80},
    "14_days": {"rub": 400, "usd": 4.49},
    "30_days": {"rub": 700, "usd": 7.85},
    "60_days": {"rub": 1300, "usd": 14.58}
}

bot = telebot.TeleBot(TOKEN)

def ensure_files_exist():
    for file in ['users.json', 'kanal.json', 'purchases.json', 'ban.json']:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                json.dump({} if file != 'kanal.json' else [], f, ensure_ascii=False)

def load_json(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {file}: {e}")
        return {} if file != 'kanal.json' else []

def save_json(file, data):
    try:
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving {file}: {e}")


def register_user(user_id, username, first_name):
    users = load_json('users.json')
    user_id_str = str(user_id)
    if user_id_str not in users:
        users[user_id_str] = {
            "username": username or "Нет юзернейма",
            "name": first_name or "Пользователь",
            "status": "Админ" if user_id in ADMIN_IDS else "Пользователь",
            "active_keys": 0,
            "purchased_keys": 0,
            "date_joined": time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_active": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    users[user_id_str]["last_active"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_json('users.json', users)
    return users[user_id_str]

def generate_random_code(length=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def is_banned(user_id):
    bans = load_json('ban.json')
    return str(user_id) in bans

def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("🧩 Поддержка", url="https://t.me/AkiraSet"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("💰 Купить подписку", callback_data="subscribe")
    )
    return keyboard

def get_subscription_keyboard(channels):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        keyboard.add(types.InlineKeyboardButton(
            f"📢 {channel.get('title', 'Канал')}",
            url=channel.get('channel_url', f"https://t.me/{channel.get('username', '')}")
        ))
    keyboard.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))
    return keyboard

def get_subscribe_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("🔑 Ключ на 1 день | 60₽ / 0.67$", callback_data="buy_1_day"),
        types.InlineKeyboardButton("🔑 Ключ на 3 дня | 150₽ / 1.68$", callback_data="buy_3_days"),
        types.InlineKeyboardButton("🔑 Ключ на 7 дней | 250₽ / 2.80$", callback_data="buy_7_days"),
        types.InlineKeyboardButton("🔑 Ключ на 14 дней | 400₽ / 4.49$", callback_data="buy_14_days"),
        types.InlineKeyboardButton("🔑 Ключ на 30 дней | 700₽ / 7.85$", callback_data="buy_30_days"),
        types.InlineKeyboardButton("🔑 Ключ на 60 дней | 1300₽ / 14.58$", callback_data="buy_60_days"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    )
    return keyboard

def get_payment_method_keyboard(product):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("💸 CryptoBot", callback_data=f"pay_cryptobot_{product}"),
        types.InlineKeyboardButton("💳 Т-БАНК", callback_data=f"pay_tbank_{product}"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="subscribe")
    )
    return keyboard

def get_cryptobot_payment_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("💳 Оплатить", url="http://t.me/send?start=IVjCAy0ppfMf"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="subscribe")
    )
    return keyboard

def get_admin_purchase_keyboard(purchase_id):
    return types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton("🚫 Отказ", callback_data=f"admin_reject_{purchase_id}"),
        types.InlineKeyboardButton("✅ Выдать", callback_data=f"admin_approve_{purchase_id}"),
        types.InlineKeyboardButton("🚫 Заблокировать", callback_data=f"admin_block_{purchase_id}")
    )

def get_admin_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("➕ Добавить канал в ОП", callback_data="admin_add_channel"),
        types.InlineKeyboardButton("➖ Удалить канал из ОП", callback_data="admin_remove_channel"),
        types.InlineKeyboardButton("📋 Список каналов ОП", callback_data="admin_list_channels"),
        types.InlineKeyboardButton("🚫 Забанить пользователя", callback_data="admin_ban_user"),
        types.InlineKeyboardButton("✅ Разбанить пользователя", callback_data="admin_unban_user"),
        types.InlineKeyboardButton("📊 Статистика бота", callback_data="admin_stats")
    )
    return keyboard

def check_user_subscriptions(user_id):
    channels = load_json('kanal.json')
    if not channels:
        return []
    not_subscribed = []
    for channel in channels:
        channel_id = channel.get('channel_id')
        if not channel_id:
            continue
        try:
            chat_member = bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if chat_member.status in ['left', 'kicked', 'restricted']:
                not_subscribed.append(channel)
        except Exception as e:
            logger.error(f"Error checking subscription for channel {channel_id}: {e}")
            continue
    return not_subscribed

@bot.message_handler(commands=['start'])
def start_command(message):
    if is_banned(message.from_user.id):
        return 
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username, message.from_user.first_name)
    not_subscribed = check_user_subscriptions(user_id)
    text = "<b>⚠️ Для использования бота подпишитесь на каналы:</b>" if not_subscribed else "<b>✨ Выберите категорию:</b>"
    markup = get_subscription_keyboard(not_subscribed) if not_subscribed else get_main_keyboard()
    try:
        bot.send_photo(message.chat.id, WELCOME_PHOTO, caption=text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error sending start message: {e}")
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription_callback(call):
    if is_banned(call.from_user.id):
        return
    not_subscribed = check_user_subscriptions(call.from_user.id)
    current_caption = call.message.caption or ""
    new_caption = "<b>⚠️ Подпишитесь на все каналы:</b>" if not_subscribed else "<b>✨ Выберите категорию:</b>"
    new_markup = get_subscription_keyboard(not_subscribed) if not_subscribed else get_main_keyboard()
    
    if current_caption != new_caption or str(call.message.reply_markup) != str(new_markup):
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=new_caption,
                reply_markup=new_markup,
                parse_mode="HTML"
            )
            bot.answer_callback_query(call.id, "✅ Подписка подтверждена!" if not not_subscribed else "❌ Вы не подписаны!")
        except Exception as e:
            logger.error(f"Error updating subscription message: {e}")
    else:
        bot.answer_callback_query(call.id, "✅ Уже подтверждено!" if not not_subscribed else "❌ Подпишитесь!")

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile_callback(call):
    if is_banned(call.from_user.id):
        return
    user_id = call.from_user.id
    not_subscribed = check_user_subscriptions(user_id)
    if not_subscribed:
        bot.answer_callback_query(call.id, "❌ Требуется подписка!")
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="<b>⚠️ Подпишитесь на каналы:</b>",
            reply_markup=get_subscription_keyboard(not_subscribed),
            parse_mode="HTML"
        )
        return
    users = load_json('users.json')
    user_data = users.get(str(user_id), register_user(user_id, call.from_user.username, call.from_user.first_name))
    profile_text = (
        f"<b>✨ Ваш профиль</b>\n\n"
        f"<b>Имя:</b> {user_data['name']}\n"
        f"<b>Telegram ID:</b> <code>{user_id}</code>\n"
        f"<b>Статус:</b> {user_data['status']}\n"
        f"<b>Активные ключи:</b> {'✅ есть' if user_data['active_keys'] > 0 else '❌ нету'}\n"
        f"<b>Купленных ключей:</b> 🔑 {user_data['purchased_keys']}"
    )
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                media=types.InputMediaPhoto(photos.photos[0][-1].file_id, caption=profile_text, parse_mode="HTML"),
                reply_markup=get_main_keyboard()
            )
        else:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_video(call.message.chat.id, DEFAULT_AVATAR, caption=profile_text, reply_markup=get_main_keyboard(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in profile callback: {e}")
        bot.send_message(call.message.chat.id, profile_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "subscribe")
def subscribe_callback(call):
    if is_banned(call.from_user.id):
        return
    not_subscribed = check_user_subscriptions(call.from_user.id)
    if not_subscribed:
        bot.answer_callback_query(call.id, "❌ Требуется подписка!")
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="<b>⚠️ Подпишитесь на каналы:</b>",
            reply_markup=get_subscription_keyboard(not_subscribed),
            parse_mode="HTML"
        )
    else:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="<b>💰 Выберите подписку:</b>",
            reply_markup=get_subscribe_keyboard(),
            parse_mode="HTML"
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_callback(call):
    if is_banned(call.from_user.id):
        return
    try:
        product = call.data.replace("buy_", "")  # Например, "1_day"
        if product not in PRICES:
            raise ValueError("Неверный продукт")
        days = product.split("_")[0]
        price_rub = PRICES[product]["rub"]
        price_usd = PRICES[product]["usd"]
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"<b>🔑 Покупка ключа на {days} {'день' if days == '1' else 'дней'} | {price_rub}₽ / {price_usd}$</b>\n\n<b>Выберите способ оплаты:</b>",
            reply_markup=get_payment_method_keyboard(product),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in buy_callback: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при выборе подписки!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_cryptobot_"))
def pay_cryptobot_callback(call):
    if is_banned(call.from_user.id):
        return
    try:
        product = call.data.replace("pay_cryptobot_", "") 
        if product not in PRICES:
            raise ValueError("Неверный продукт")
        days = product.split("_")[0]
        price_rub = PRICES[product]["rub"]
        price_usd = PRICES[product]["usd"]
        random_code = generate_random_code()
        caption = (
            f"<b>💸 Оплата через CryptoBot</b>\n\n"
            f"<b>🔑 Ключ на {days} {'день' if days == '1' else 'дней'}</b>\n"
            f"<b>Стоимость:</b> {price_rub}₽ ≈ {price_usd}$ (курс {USD_RATE}₽/$)\n\n"
            f"<b>Важно:</b> Укажите в описании <code>{random_code}</code>\n"
            f"<b>📱 После оплаты пришлите скриншот</b>"
        )
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=caption,
            reply_markup=get_cryptobot_payment_keyboard(),
            parse_mode="HTML"
        )
        purchases = load_json('purchases.json')
        purchases[str(call.message.message_id)] = {
            "user_id": call.from_user.id,
            "username": call.from_user.username or "Нет юзернейма",
            "product": product,
            "price_rub": price_rub,
            "price_usd": price_usd,
            "code": random_code,
            "method": "CryptoBot",
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_json('purchases.json', purchases)
    except Exception as e:
        logger.error(f"Error in pay_cryptobot_callback: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при обработке оплаты!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_tbank_"))
def pay_tbank_callback(call):
    if is_banned(call.from_user.id):
        return
    try:
        product = call.data.replace("pay_tbank_", "")
        if product not in PRICES:
            raise ValueError("Неверный продукт")
        days = product.split("_")[0]
        price_rub = PRICES[product]["rub"]
        price_usd = PRICES[product]["usd"]
        random_code = generate_random_code()
        caption = (
            f"<b>💳 Оплата через Т-БАНК</b>\n\n"
            f"<b>🔑 Ключ на {days} {'день' if days == '1' else 'дней'}</b>\n"
            f"<b>Стоимость:</b> {price_rub}₽ ≈ {price_usd}$ (курс {USD_RATE}₽/$)\n"
            f"💳 <b>Карта:</b> <code>2200700537645490</code>\n"
            f"<b>Имя:</b> Никита К.\n\n"
            f"<b>Важно:</b> Укажите в описании <code>{random_code}</code>\n"
            f"<b>📱 После оплаты пришлите чек</b>"
        )
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=caption,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 Назад", callback_data="subscribe")
            ),
            parse_mode="HTML"
        )
        purchases = load_json('purchases.json')
        purchases[str(call.message.message_id)] = {
            "user_id": call.from_user.id,
            "username": call.from_user.username or "Нет юзернейма",
            "product": product,
            "price_rub": price_rub,
            "price_usd": price_usd,
            "code": random_code,
            "method": "Т-БАНК",
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_json('purchases.json', purchases)
    except Exception as e:
        logger.error(f"Error in pay_tbank_callback: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при обработке оплаты!")

@bot.message_handler(content_types=['photo'])
def handle_payment_proof(message):
    if is_banned(message.from_user.id):
        return
    purchases = load_json('purchases.json')
    if not isinstance(purchases, dict):
        purchases = {}
        save_json('purchases.json', purchases)
    
    purchase = None
    for msg_id, data in purchases.items():
        if data["user_id"] == message.from_user.id and "processed" not in data:
            purchase = data
            purchase["msg_id"] = msg_id
            break
    
    if not purchase:
        bot.reply_to(message, "<b>❌ Покупка не найдена!</b>\nУбедитесь, что вы выбрали способ оплаты и отправили фото чека.", parse_mode="HTML")
        return
    
    try:
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(
            message.chat.id,
            "<b>✅ Ваша покупка рассматривается</b>\nОбычно это занимает от 30 минут до 7 часов.",
            parse_mode="HTML"
        )
        
        admin_text = (
            f"<b>‼️ Новая покупка</b>\n"
            f"• <b>👤 Username:</b> @{purchase['username']}\n"
            f"• <b>🆔 Telegram ID:</b> {purchase['user_id']}\n"
            f"• <b>🛍 Товар:</b> Ключ на {purchase['product'].split('_')[0]} {'день' if purchase['product'].split('_')[0] == '1' else 'дней'}\n"
            f"• <b>💰 Стоимость:</b> {purchase['price_rub']}₽ / {purchase['price_usd']}$\n"
            f"• <b>📝 Код:</b> {purchase['code']}\n"
            f"• <b>💳 Способ оплаты:</b> {purchase['method']}\n"
            f"• <b>🕐 Время (МСК):</b> {purchase['time']}"
        )
        for admin_id in ADMIN_IDS:
            try:
                bot.send_photo(
                    admin_id,
                    message.photo[-1].file_id,
                    caption=admin_text,
                    reply_markup=get_admin_purchase_keyboard(purchase["msg_id"]),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error sending to admin {admin_id}: {e}")
    except Exception as e:
        logger.error(f"Error in handle_payment_proof: {e}")
        bot.send_message(message.chat.id, "<b>❌ Ошибка при обработке чека! Попробуйте снова.</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_reject_"))
def admin_reject_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    purchase_id = call.data.split("_")[2]
    purchases = load_json('purchases.json')
    if purchase_id in purchases:
        purchase = purchases[purchase_id]
        bot.send_message(
            purchase["user_id"],
            "<b>🚫 Что-то пошло не так</b>\nВозможно, чек поддельный или вы не указали описание к оплате. Для решения вопроса напишите @AkiraSet.",
            parse_mode="HTML"
        )
        purchases[purchase_id]["processed"] = "rejected"
        save_json('purchases.json', purchases)
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"{call.message.caption}\n\n<b>🚫 Отказано</b>",
            parse_mode="HTML"
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_approve_"))
def admin_approve_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    purchase_id = call.data.split("_")[2]
    purchases = load_json('purchases.json')
    if purchase_id in purchases:
        purchase = purchases[purchase_id]
        purchase["admin_text"] = (
            f"<b>‼️ Новая покупка</b>\n"
            f"• <b>👤 Username:</b> @{purchase['username']}\n"
            f"• <b>🆔 Telegram ID:</b> {purchase['user_id']}\n"
            f"• <b>🛍 Товар:</b> Ключ на {purchase['product'].split('_')[0]} {'день' if purchase['product'].split('_')[0] == '1' else 'дней'}\n"
            f"• <b>💰 Стоимость:</b> {purchase['price_rub']}₽ / {purchase['price_usd']}$\n"
            f"• <b>📝 Код:</b> {purchase['code']}\n"
            f"• <b>💳 Способ оплаты:</b> {purchase['method']}\n"
            f"• <b>🕐 Время (МСК):</b> {purchase['time']}"
        )
        save_json('purchases.json', purchases)
        bot.send_message(
            call.from_user.id,
            f"<b>🔑 Отправьте ключ для {purchase['product']}:</b>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler_by_chat_id(call.from_user.id, lambda msg: send_key(msg, purchase, purchase_id))

def send_key(message, purchase, purchase_id):
    if message.from_user.id not in ADMIN_IDS:
        return
    key = message.text.strip()
    if not key:
        bot.reply_to(message, "<b>❌ Ключ не может быть пустым!</b>", parse_mode="HTML")
        return
    bot.send_photo(
        purchase["user_id"],
        KEY_IMAGES[purchase["product"]],
        caption=f"<b>✅ Спасибо за покупку!</b>\nВаш ключ:\n<code>{key}</code>",
        parse_mode="HTML"
    )
    purchases = load_json('purchases.json')
    purchases[purchase_id]["processed"] = "approved"
    purchases[purchase_id]["key"] = key
    save_json('purchases.json', purchases)
    
    users = load_json('users.json')
    user_id_str = str(purchase["user_id"])
    if user_id_str in users:
        users[user_id_str]["purchased_keys"] += 1
        users[user_id_str]["active_keys"] += 1  # Предполагаем, что ключ сразу активен
        save_json('users.json', users)
    
    for admin_id in ADMIN_IDS:
        try:
            bot.edit_message_caption(
                chat_id=admin_id,
                message_id=int(purchase["msg_id"]),
                caption=f"{purchases[purchase_id]['admin_text']}\n\n<b>✅ Выдано</b>",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error updating message for admin {admin_id}: {e}")
    
    bot.send_message(
        message.chat.id,
        f"<b>✅ Ключ выдан для {purchase['product']}</b>",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_block_"))
def admin_block_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    purchase_id = call.data.split("_")[2]
    purchases = load_json('purchases.json')
    if purchase_id in purchases:
        purchase = purchases[purchase_id]
        user_id = str(purchase["user_id"])
        bans = load_json('ban.json')
        bans[user_id] = {
            "username": purchase["username"],
            "banned_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "reason": "Нарушение правил (через покупку)"
        }
        save_json('ban.json', bans)
        
        bot.send_message(
            purchase["user_id"],
            "<b>🚫 Ваш аккаунт заблокирован за нарушение правил!</b>",
            parse_mode="HTML"
        )
        purchases[purchase_id]["processed"] = "blocked"
        save_json('purchases.json', purchases)
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"{call.message.caption}\n\n<b>🚫 Забанен</b>",
            parse_mode="HTML"
        )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_callback(call):
    if is_banned(call.from_user.id):
        return
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption="<b>✨ Выберите категорию:</b>",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "<b>⛔ У вас нет доступа!</b>", parse_mode="HTML")
        return
    bot.send_message(
        message.chat.id,
        "<b>👑 Администрирование</b>\n\nВыберите действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_channel")
def admin_add_channel_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    msg = bot.send_message(call.message.chat.id, "<b>📝 Отправьте ID канала, ссылку и название через пробел</b>\nПример: <code>-100123456789 https://t.me/channel Канал</code>", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_add_channel)

def process_add_channel(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        parts = message.text.split(" ", 2)
        if len(parts) != 3:
            bot.reply_to(message, "<b>❌ Неверный формат!</b>\nПример: <code>-100123456789 https://t.me/channel Канал</code>", parse_mode="HTML")
            return
        channel_id, channel_url, channel_title = parts
        bot.get_chat(channel_id) 
        channels = load_json('kanal.json')
        if any(ch.get('channel_id') == channel_id for ch in channels):
            bot.reply_to(message, f"<b>⚠️ Канал {channel_title} уже добавлен!</b>", parse_mode="HTML")
            return
        channels.append({
            "channel_id": channel_id,
            "channel_url": channel_url,
            "title": channel_title,
            "added_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        save_json('kanal.json', channels)
        bot.reply_to(message, f"<b>✅ Канал {channel_title} добавлен!</b>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        bot.reply_to(message, f"<b>❌ Ошибка:</b> {str(e)}", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_remove_channel")
def admin_remove_channel_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    channels = load_json('kanal.json')
    if not channels:
        bot.edit_message_text("<b>⚠️ Список каналов пуст!</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        return
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for i, channel in enumerate(channels):
        keyboard.add(types.InlineKeyboardButton(f"{i+1}. {channel['title']}", callback_data=f"remove_channel_{i}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    bot.edit_message_text("<b>🗑️ Выберите канал для удаления:</b>", call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_channel_"))
def remove_specific_channel_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    try:
        idx = int(call.data.split("_")[2])
        channels = load_json('kanal.json')
        if idx < len(channels):
            removed = channels.pop(idx)
            save_json('kanal.json', channels)
            bot.edit_message_text(
                f"<b>✅ Канал {removed['title']} удален!</b>\n\nВыберите действие:",
                call.message.chat.id, call.message.message_id,
                reply_markup=get_admin_keyboard(),
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error removing channel: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_list_channels")
def admin_list_channels_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    channels = load_json('kanal.json')
    text = "<b>📋 Список каналов:</b>\n\n" + (
        "\n".join(f"{i+1}. <b>{ch['title']}</b> ({ch['channel_id']})" for i, ch in enumerate(channels)) or "❌ Пусто"
    )
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban_user")
def admin_ban_user_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    msg = bot.send_message(call.message.chat.id, "<b>🚫 Введите Telegram ID пользователя для бана:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_ban_user)

def process_ban_user(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        user_id = message.text.strip()
        if not user_id.isdigit():
            bot.reply_to(message, "<b>❌ ID должен быть числом!</b>", parse_mode="HTML")
            return
        user_id = str(user_id)
        if int(user_id) in ADMIN_IDS:
            bot.reply_to(message, "<b>❌ Нельзя забанить админа!</b>", parse_mode="HTML")
            return
        bans = load_json('ban.json')
        if user_id in bans:
            bot.reply_to(message, "<b>⚠️ Пользователь уже забанен!</b>", parse_mode="HTML")
            return
        users = load_json('users.json')
        username = users.get(user_id, {}).get("username", "Неизвестно")
        bans[user_id] = {
            "username": username,
            "banned_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "reason": "Ручной бан админом"
        }
        save_json('ban.json', bans)
        bot.reply_to(message, f"<b>✅ Пользователь {username} (ID: {user_id}) забанен!</b>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        bot.reply_to(message, f"<b>❌ Ошибка:</b> {str(e)}", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_unban_user")
def admin_unban_user_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    msg = bot.send_message(call.message.chat.id, "<b>✅ Введите Telegram ID пользователя для разбана:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_unban_user)

def process_unban_user(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        user_id = message.text.strip()
        if not user_id.isdigit():
            bot.reply_to(message, "<b>❌ ID должен быть числом!</b>", parse_mode="HTML")
            return
        user_id = str(user_id)
        bans = load_json('ban.json')
        if user_id not in bans:
            bot.reply_to(message, "<b>⚠️ Пользователь не забанен!</b>", parse_mode="HTML")
            return
        username = bans[user_id]["username"]
        del bans[user_id]
        save_json('ban.json', bans)
        bot.reply_to(message, f"<b>✅ Пользователь {username} (ID: {user_id}) разбанен!</b>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        bot.reply_to(message, f"<b>❌ Ошибка:</b> {str(e)}", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    purchases = load_json('purchases.json')
    users = load_json('users.json')
    bans = load_json('ban.json')
    
    total_keys = sum(1 for p in purchases.values() if p.get("processed") == "approved")
    month_start = datetime.now() - timedelta(days=30)
    tbank_month = sum(p["price_rub"] for p in purchases.values() if p.get("processed") == "approved" and p["method"] == "Т-БАНК" and datetime.strptime(p["time"], "%Y-%m-%d %H:%M:%S") >= month_start)
    crypto_month = sum(p["price_rub"] for p in purchases.values() if p.get("processed") == "approved" and p["method"] == "CryptoBot" and datetime.strptime(p["time"], "%Y-%m-%d %H:%M:%S") >= month_start)
    total_users = len(users)
    banned_users = len(bans)
    
    stats_text = (
        f"<b>📊 Статистика бота</b>\n\n"
        f"• <b>Всего ключей куплено:</b> {total_keys}\n"
        f"• <b>Заработано за месяц (Т-БАНК):</b> {tbank_month}₽\n"
        f"• <b>Заработано за месяц (CryptoBot):</b> {crypto_month}₽\n"
        f"• <b>Всего пользователей:</b> {total_users}\n"
        f"• <b>Забаненных пользователей:</b> {banned_users}"
    )
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    bot.edit_message_text(
        "<b>👑 Администрирование</b>\n\nВыберите действие:",
        call.message.chat.id, call.message.message_id,
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

if __name__ == "__main__":
    logger.info("🚀 Бот запущен")
    ensure_files_exist()
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            logger.error(f"🔥 Бот упал: {e}")
            time.sleep(10)