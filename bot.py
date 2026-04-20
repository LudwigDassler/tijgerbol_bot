#!/usr/bin/env python3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import re
import logging
import ssl
from urllib.parse import quote
import time

ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BOT_TOKEN = '8122009360:AAHY5R78f6_7NifIMmw2w3lzgcyGkzkulTc'
SUPABASE_URL = 'https://iisgrrjkxryteofebutu.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlpc2dycmpreHJ5dGVvZmVidXR1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU4MzM1MjMsImV4cCI6MjA5MTQwOTUyM30.RfdjJuUvpqY0ML0SKcxfZs4PyjUo0zm5oA0i6OntCvU'

bot = telebot.TeleBot(BOT_TOKEN)
headers = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Content-Type': 'application/json'}

user_sessions = {}

COUNTRIES = {
    'ru': {'name': 'Россия', 'code': '+7'},
    'ua': {'name': 'Украина', 'code': '+380'},
    'by': {'name': 'Беларусь', 'code': '+375'},
    'kz': {'name': 'Казахстан', 'code': '+7'},
}

def normalize_phone(phone_raw, country='ru'):
    digits = re.sub(r'\D', '', phone_raw)
    if phone_raw.startswith('+'): return phone_raw
    code = COUNTRIES.get(country, COUNTRIES['ru'])['code']
    if code == '+7':
        if len(digits) == 10: return '+7' + digits
        if len(digits) == 11 and digits.startswith('8'): return '+7' + digits[1:]
        if len(digits) == 11 and digits.startswith('7'): return '+' + digits
    elif code == '+380':
        if len(digits) == 9: return '+380' + digits
        if len(digits) == 12 and digits.startswith('380'): return '+' + digits
    elif code == '+375':
        if len(digits) == 9: return '+375' + digits
        if len(digits) == 12 and digits.startswith('375'): return '+' + digits
    return f'+{digits}'

def get_user_by_phone(phone_raw, country='ru'):
    phone = normalize_phone(phone_raw, country)
    try:
        resp = requests.get(f"{SUPABASE_URL}/rest/v1/users?phone=eq.{quote(phone)}&select=*", headers=headers, timeout=5)
        if resp.status_code == 200 and resp.json():
            return resp.json()[0]
    except Exception as e:
        logging.error(f"Ошибка поиска: {e}")
    return None

def get_level(spent):
    if spent >= 10000: return 'Платиновый'
    if spent >= 5000: return 'Золотой'
    if spent >= 2000: return 'Серебряный'
    return 'Бронзовый'

def country_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    for key, country in COUNTRIES.items():
        kb.add(InlineKeyboardButton(country['name'], callback_data=f"country_{key}"))
    return kb

def main_menu(phone=None):
    kb = InlineKeyboardMarkup(row_width=2)
    if phone:
        kb.add(InlineKeyboardButton("💰 Баланс", callback_data=f"bal_{phone}"), 
               InlineKeyboardButton("📜 История", callback_data=f"hist_{phone}"))
        kb.add(InlineKeyboardButton("➕ Начислить", callback_data=f"add_{phone}"), 
               InlineKeyboardButton("➖ Списать", callback_data=f"sub_{phone}"))
        kb.add(InlineKeyboardButton("🔄 Сменить", callback_data="change"))
    else:
        kb.add(InlineKeyboardButton("🔑 Войти", callback_data="login"))
    kb.add(InlineKeyboardButton("❓ Помощь", callback_data="help"))
    return kb

def back_menu(phone):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data=f"back_{phone}"))
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    user_sessions.pop(m.chat.id, None)
    bot.send_message(m.chat.id, "🦒 Tijgerbol\n\nВыберите страну:", reply_markup=country_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("country_"))
def choose_country(c):
    country = c.data.split("_")[1]
    user_sessions[c.message.chat.id] = {'country': country}
    bot.edit_message_text(f"✅ Страна: {COUNTRIES[country]['name']}\n\nНажмите 'Войти'", 
                         c.message.chat.id, c.message.message_id, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "login")
def login_prompt(c):
    bot.send_message(c.message.chat.id, "📞 Отправьте номер телефона:")
    bot.register_next_step_handler(c.message, process_login)

def process_login(m):
    s = user_sessions.get(m.chat.id, {})
    country = s.get('country', 'ru')
    user = get_user_by_phone(m.text.strip(), country)
    if user:
        s['phone'] = user['phone']
        user_sessions[m.chat.id] = s
        bot.send_message(m.chat.id,
            f"✅ Вы вошли как {user.get('nickname', 'Гость')}\n🎁 {user.get('bonus', 0)} бонусов\n💰 {user.get('spent', 0)}₽\n🏆 {get_level(user.get('spent', 0))}",
            reply_markup=main_menu(user['phone']))
    else:
        bot.send_message(m.chat.id, f"❌ Пользователь не найден\nЗарегистрируйтесь: https://ludwigdassler.github.io/tijgerbol_app/", 
                        reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("bal_"))
def balance(c):
    phone = c.data.split("_", 1)[1]
    user = get_user_by_phone(phone)
    if user:
        bot.edit_message_text(
            f"🦒 {user.get('nickname', 'Гость')}\n🎁 {user.get('bonus', 0)} бонусов\n💰 {user.get('spent', 0)}₽\n🏆 {get_level(user.get('spent', 0))}",
            c.message.chat.id, c.message.message_id, reply_markup=back_menu(phone))
    else:
        bot.edit_message_text("❌ Ошибка", c.message.chat.id, c.message.message_id, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("hist_"))
def history(c):
    phone = c.data.split("_", 1)[1]
    user = get_user_by_phone(phone)
    if user:
        try:
            resp = requests.get(f"{SUPABASE_URL}/rest/v1/transactions?phone=eq.{quote(user['phone'])}&order=created_at.desc&limit=10", 
                               headers=headers, timeout=5)
            tx = resp.json() if resp.status_code == 200 else []
            if tx:
                text = "📜 История:\n"
                for t in tx:
                    sign = '+' if t['amount'] > 0 else ''
                    text += f"{t['created_at'][:16]} {sign}{t['amount']}\n"
                bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=back_menu(phone))
            else:
                bot.edit_message_text("📭 Нет операций", c.message.chat.id, c.message.message_id, reply_markup=back_menu(phone))
        except:
            bot.edit_message_text("❌ Ошибка", c.message.chat.id, c.message.message_id, reply_markup=back_menu(phone))
    else:
        bot.edit_message_text("❌ Ошибка", c.message.chat.id, c.message.message_id, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("add_"))
def add_prompt(c):
    phone = c.data.split("_", 1)[1]
    msg = bot.send_message(c.message.chat.id, "💵 Сумма покупки:")
    bot.register_next_step_handler(msg, process_add, phone)

def process_add(m, phone):
    try:
        amt = int(m.text.strip())
        if amt <= 0: raise ValueError
    except:
        bot.send_message(m.chat.id, "❌ Ошибка", reply_markup=main_menu(phone))
        return
    user = get_user_by_phone(phone)
    if not user:
        bot.send_message(m.chat.id, "❌ Ошибка", reply_markup=main_menu())
        return
    bonus = int(amt * 0.05)
    new_bonus = user['bonus'] + bonus
    new_spent = user['spent'] + amt
    try:
        requests.patch(f"{SUPABASE_URL}/rest/v1/users?phone=eq.{quote(user['phone'])}", headers=headers, 
                      json={'bonus': new_bonus, 'spent': new_spent}, timeout=5)
        requests.post(f"{SUPABASE_URL}/rest/v1/transactions", headers=headers,
                     json={'phone': user['phone'], 'amount': bonus, 'type': 'add', 
                           'description': f'🤖 Бот: {amt}₽ → +{bonus}'}, timeout=5)
        bot.send_message(m.chat.id, f"✅ +{bonus} бонусов\n🎁 Теперь {new_bonus}", reply_markup=main_menu(phone))
    except:
        bot.send_message(m.chat.id, "❌ Ошибка", reply_markup=main_menu(phone))

@bot.callback_query_handler(func=lambda c: c.data.startswith("sub_"))
def sub_prompt(c):
    phone = c.data.split("_", 1)[1]
    msg = bot.send_message(c.message.chat.id, "💸 Введите сумму для списания (любое число):")
    bot.register_next_step_handler(msg, process_sub, phone)

def process_sub(m, phone):
    try:
        amount = int(m.text.strip())
        if amount <= 0: raise ValueError
    except:
        bot.send_message(m.chat.id, "❌ Введите корректное число", reply_markup=main_menu(phone))
        return
    
    user = get_user_by_phone(phone)
    if not user:
        bot.send_message(m.chat.id, "❌ Пользователь не найден", reply_markup=main_menu())
        return
    
    if user['bonus'] >= amount:
        new_bonus = user['bonus'] - amount
        try:
            requests.patch(f"{SUPABASE_URL}/rest/v1/users?phone=eq.{quote(user['phone'])}", headers=headers, 
                          json={'bonus': new_bonus}, timeout=5)
            requests.post(f"{SUPABASE_URL}/rest/v1/transactions", headers=headers,
                         json={'phone': user['phone'], 'amount': -amount, 'type': 'remove', 
                               'description': f'🤖 Списано {amount} бонусов'}, timeout=5)
            bot.send_message(m.chat.id, f"✅ Списано {amount} бонусов!\n🎁 Осталось: {new_bonus}", 
                            reply_markup=main_menu(phone))
        except:
            bot.send_message(m.chat.id, "❌ Ошибка при списании", reply_markup=main_menu(phone))
    else:
        bot.send_message(m.chat.id, f"❌ Недостаточно бонусов! У вас {user['bonus']}", 
                        reply_markup=main_menu(phone))

@bot.callback_query_handler(func=lambda c: c.data == "change")
def change(c):
    user_sessions.pop(c.message.chat.id, None)
    bot.edit_message_text("🦒 Выберите страну:", c.message.chat.id, c.message.message_id, reply_markup=country_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("back_"))
def back(c):
    phone = c.data.split("_", 1)[1]
    user = get_user_by_phone(phone)
    if user:
        bot.edit_message_text(f"🦒 Главное меню\n🎁 {user.get('bonus', 0)} бонусов", 
                             c.message.chat.id, c.message.message_id, reply_markup=main_menu(phone))
    else:
        bot.edit_message_text("🦒 Главное меню", c.message.chat.id, c.message.message_id, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "help")
def help_menu(c):
    bot.edit_message_text(
        "🦒 Помощь\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔑 Войти - выбор страны и вход по номеру\n"
        "💰 Баланс - бонусы и уровень\n"
        "📜 История - последние операции\n"
        "➕ Начислить - 5% за покупку\n"
        "➖ Списать - списание любой суммы\n"
        "🔄 Сменить - смена пользователя\n━━━━━━━━━━━━━━━━━━━━━━━",
        c.message.chat.id, c.message.message_id, reply_markup=main_menu())

if __name__ == '__main__':
    logging.info("✅ Бот запущен!")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logging.error(f"Ошибка: {e}")
            time.sleep(10)
