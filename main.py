import telebot
import sqlite3
import random
import os
import shutil
from datetime import datetime
# Токен бота
TOKEN = '6122431243:AAEN3UVYQSnW22yB3j7PXKStpyUgeryGedA'
bot = telebot.TeleBot(TOKEN)
jokes = [
    "Почему программисты так не любят море? Потому что в нем нет интерфейса!",
    "Какая разница между Илоном и Android? Один робот, другой операционка.",
    "Какой самый трудный вопрос для программиста? Что вы хотите поесть? ",
    "Планы на выходные: спать до обеда. Реальность: просыпаться в 6 утра, потому что обед закончился.",
    "План на день: быть продуктивным. Реальность: просматривать мемы весь день ", "План на сегодня: быть на высоте. План на завтра: взять с собой лестницу ",
    "Планирование - это когда ты вставляешь в календарь важные дела, а потом неделя проходит, и ты всё равно ничего не делаешь.",
    "Я сделал план, чтобы следовать плану, но планы изменились, и теперь у меня новый план, чтобы справиться с этими планами. ",
    "Что делает пчела в спортзале? Жужжит на беговой дорожке! ",
    "Какой ключ открывает дверь в будущее? Телескопический. ",
]

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('plans.db')  # Создаем новое соединение
    cursor = conn.cursor()

    # Создаем таблицу plans, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            user_id INTEGER,
            day TEXT,
            plan TEXT,
            PRIMARY KEY (user_id, day)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            first_name TEXT,
            last_name TEXT,
            review_text TEXT
        )
    ''')
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                days_created INTEGER DEFAULT 0
            )
        ''')
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()
    # Создаем inline клавиатуру с кнопками "Новый план" и "Мои планы"
    markup = telebot.types.InlineKeyboardMarkup()
    new_plan_button = telebot.types.InlineKeyboardButton(text="📝 Новый план", callback_data="new_plan")  # Вот здесь добавляем кнопку
    my_plans_button = telebot.types.InlineKeyboardButton(text="📅 Мои планы", callback_data="my_plans")
    leave_review_button = telebot.types.InlineKeyboardButton(text="📝 Оставить отзыв", callback_data="leave_review")
    markup.add(new_plan_button, my_plans_button, leave_review_button)

    bot.send_message(message.chat.id, "👋 Привет! Бот Planerka готов помогать вам с вашими планами!😊\nВыберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'new_plan')
def new_plan_callback(call):
    user_id = call.from_user.id
    msg = bot.send_message(user_id, "Введите день:")
    bot.register_next_step_handler(msg, process_day_step)

def process_day_step(message):
    user_id = message.from_user.id
    day = message.text

    msg = bot.send_message(user_id, "Введите свои планы:")
    bot.register_next_step_handler(msg, lambda msg: process_plan_step(user_id, day, msg))

def process_plan_step(user_id, day, message):
    plan = message.text

    conn = sqlite3.connect('plans.db')
    cursor = conn.cursor()

    # Вставляем данные в таблицу plans + считаем дни
    cursor.execute('INSERT OR REPLACE INTO plans (user_id, day, plan) VALUES (?, ?, ?)', (user_id, day, plan))
    cursor.execute('UPDATE users SET days_created = days_created + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    markup = telebot.types.InlineKeyboardMarkup()
    view_plans_button = telebot.types.InlineKeyboardButton(text="📅 Посмотреть мои планы", callback_data="my_plans")
    markup.add(view_plans_button)

    bot.send_message(user_id, "✅  Планы успешно сохранены! Что вы хотите сделать дальше?", reply_markup=markup)

# Обработчик кнопки "Мои планы"
@bot.callback_query_handler(func=lambda call: call.data == 'my_plans')
def my_plans_callback(call):
    user_id = call.from_user.id

    conn = sqlite3.connect('plans.db')
    cursor = conn.cursor()
    try:
        # Получаем планы пользователя
        cursor.execute('SELECT day, plan FROM plans WHERE user_id = ?', (user_id,))
        user_plans = cursor.fetchall()

        conn.close()

        if user_plans:
            plans_text = "📔 Ваши планы: 📔\n"
            for day, plan in user_plans:
                plans_text += f"{day} : {plan}\n"
        else:
            plans_text = "У вас пока нет планов."

        markup = telebot.types.InlineKeyboardMarkup()
        return_button = telebot.types.InlineKeyboardButton(text="↩️ Вернуться", callback_data="return_to_start")
        delete_plans_button = telebot.types.InlineKeyboardButton(text="🗑️ Удалить расписание", callback_data="delete_plans")  # Новая кнопка
        markup.add(return_button, delete_plans_button)
        bot.send_message(user_id, plans_text, reply_markup=markup)
    except sqlite3.Error as e:
        # Обработка ошибок
        print("Ошибка при выполнении SQL-запроса:", e)

# Обработчик кнопки "Вернуться"
@bot.callback_query_handler(func=lambda call: call.data == 'return_to_start')
def return_to_start_callback(call):
    user_id = call.from_user.id

    markup = telebot.types.InlineKeyboardMarkup()
    new_plan_button = telebot.types.InlineKeyboardButton(text="📝 Новый план", callback_data="new_plan")
    view_plans_button = telebot.types.InlineKeyboardButton(text="📅 Посмотреть мои планы", callback_data="my_plans")  # Изменили название кнопки
    leave_review_button = telebot.types.InlineKeyboardButton(text=" Оставить отзыв", callback_data="leave_review")
    markup.add(new_plan_button, view_plans_button, leave_review_button)  # Добавили новую кнопку

    bot.send_message(user_id, "Бот Planerka вновь готов помогать вам с вашими планами!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'delete_plans')
def delete_plans_callback(call):
    user_id = call.from_user.id

    conn = sqlite3.connect('plans.db')
    cursor = conn.cursor()

    # Удаляем расписание пользователя
    cursor.execute('DELETE FROM plans WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    markup = telebot.types.InlineKeyboardMarkup()
    new_plan_button = telebot.types.InlineKeyboardButton(text="📅 Новый план", callback_data="new_plan")
    view_plans_button = telebot.types.InlineKeyboardButton(text="📝 Посмотреть мои планы", callback_data="my_plans")
    markup.add(new_plan_button, view_plans_button)
    bot.send_message(user_id, "✅  Ваше расписание успешно удалено!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'leave_review')
def leave_review_callback(call):
    user_id = call.from_user.id
    msg = bot.send_message(user_id, "Оставьте пожалуйста свой анонимный отзыв о работе бота Planerka, а также пожелания и ваши взгляды на наш проект:")
    bot.register_next_step_handler(msg, process_review_step)

def process_review_step(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name if message.from_user.last_name else ""
    review_text = message.text

    conn = sqlite3.connect('plans.db')
    cursor = conn.cursor()

    # Вставляем отзыв в таблицу reviews
    cursor.execute('INSERT INTO reviews (user_id, first_name, last_name, review_text) VALUES (?, ?, ?, ?)',
                   (user_id, first_name, last_name, review_text))
    conn.commit()
    conn.close()

    markup = telebot.types.InlineKeyboardMarkup()
    return_button = telebot.types.InlineKeyboardButton(text="↩️ Вернуться", callback_data="return_to_start")
    markup.add(return_button)
    bot.send_message(user_id, "Спасибо за ваш отзыв!", reply_markup=markup)
@bot.message_handler(commands=['reviews'])
def read_reviews(message):
    if message.from_user.id == 1873139768:
        conn = sqlite3.connect('plans.db')
        cursor = conn.cursor()

        # Получаем все отзывы
        cursor.execute('SELECT user_id, first_name, last_name, review_text FROM reviews')
        all_reviews = cursor.fetchall()

        conn.close()

        if all_reviews:
            reviews_text = "Отзывы:\n"
            for user_id, first_name, last_name, review_text in all_reviews:
                user_name = f"{first_name} {last_name}" if last_name else first_name
                reviews_text += f"Пользователь {user_name} (ID: {user_id}):\n{review_text}\n\n"
        else:
            reviews_text = "Пока нет отзывов."

        bot.send_message(message.chat.id, reviews_text)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к отзывам.")

@bot.message_handler(commands=['check_days'])
def check_days(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('plans.db')
    cursor = conn.cursor()

    # Получаем количество уникальных дней, созданных пользователем
    cursor.execute('SELECT COUNT(DISTINCT day) FROM plans WHERE user_id = ?', (user_id,))
    days_created = cursor.fetchone()[0]


    markup = telebot.types.InlineKeyboardMarkup()
    return_button = telebot.types.InlineKeyboardButton(text="↩️ Вернуться", callback_data="return_to_start")
    markup.add(return_button)

    if days_created >= 7:
        bot.send_message(user_id, "Отлично, у вас есть планы на 7 дней! 🎉", reply_markup=markup)
        random_joke = random.choice(jokes)
        bot.send_message(user_id, random_joke)
    else:
        bot.send_message(user_id, f"У вас есть планы на такое количество дней:  {days_created} . ", reply_markup=markup)

    conn.close()

@bot.message_handler(commands=['say_everyone'])
def ask_admin_message(message):
    user_id = message.from_user.id
    if user_id == 1873139768:
        bot.send_message(user_id, "Введите сообщение для отправки всем пользователям:")
        bot.register_next_step_handler(message, process_admin_message)
    else:
        bot.send_message(user_id, "У вас нет доступа к этой команде.")

def process_admin_message(message):
    admin_message = message.text
    conn = sqlite3.connect('plans.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM users')
    all_users = cursor.fetchall()
    print("Пользователи, получившие рекламу: ", all_users)
    conn.close()

    for user in all_users:
        try:
            bot.send_message(user[0], admin_message)
        except Exception as e:
            print("Ошибка при отправке сообщения:", e)
    print('Сообщение(реклама_текст): ',admin_message)
    bot.send_message(message.from_user.id, "Сообщение успешно отправлено всем пользователям!")

@bot.message_handler(commands=['image_everyone'])
def ask_admin_image(message):
    user_id = message.from_user.id
    if user_id == 1873139768:
        bot.send_message(user_id, "Пришлите изображение для отправки всем пользователям:")
        bot.register_next_step_handler(message, process_admin_image)
    else:
        bot.send_message(user_id, "У вас нет доступа к этой команде.")
def process_admin_image(message):
    admin_image = message.photo[-1].file_id
    conn = sqlite3.connect('plans.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM users')
    all_users = cursor.fetchall()

    conn.close()

    for user in all_users:
        bot.send_photo(user[0], admin_image)

    bot.send_message(message.from_user.id, "Изображение успешно отправлено всем пользователям!")

@bot.message_handler(commands=['backup'])
def create_backup(message):
    user_id = message.from_user.id
    if user_id == 1873139768:
        backup_folder = 'backup'
        os.makedirs(backup_folder, exist_ok=True)  # Создаем папку backup, если ее нет

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_filename = f'{backup_folder}/plans_backup_{timestamp}.db'

        # Создаем копию файла базы данных
        try:
            shutil.copy('plans.db', backup_filename)
            bot.send_message(user_id, "Резервная копия успешно создана!")
        except Exception as e:
            bot.send_message(user_id, f"Произошла ошибка при создании резервной копии: {e}")
    else:
        bot.send_message(user_id, "У вас нет доступа к этой команде.")
@bot.message_handler(commands=['cooperation'])
def coop(message):
    markup = telebot.types.InlineKeyboardMarkup()
    return_button = telebot.types.InlineKeyboardButton(text="↩️ Вернуться", callback_data="return_to_start")
    markup.add(return_button)
    bot.send_message(message.chat.id, "По вопросам сотрудничества и рекламы обращайтесь:\nartemnkia@gmail.com", reply_markup=markup)

# Запуск бота
bot.polling(none_stop=True)