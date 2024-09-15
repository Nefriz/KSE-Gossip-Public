import telebot as tb
import datetime as dt
import json
import csv
import re
import time
import pandas as pd
from telebot.types import Update

tb.apihelper.Timeout = 24 * 60 * 60

config = json.load(open('config.json'))
bot = tb.TeleBot(config.get('bot'))
chanel_id = config.get('chanel_id')
feedback_path = config.get('feedback_path')
feedback_chanel = config.get('feedback_chanel')
admin_id = config.get('admin_id')
user_status = {}
last_message_time = {}  # Dictionary to track the last message time for each user

print(user_status)

users = pd.read_csv("users.csv", encoding="utf-8")

def censore(text: str) -> bool:
    with open("bad_words.txt", 'r', encoding='utf-8') as bad_file:
        bad_words = {word.strip().lower() for word in bad_file}
    text = re.sub(r'[^\w\s]', '', text)
    words = text.lower().split()

    for word in words:
        if word in bad_words:
            return False
    return True

def show_menu(chat_id: int) -> None:
    menu_text = ("Основний канал: @KSEgossip \n"
                 "Виберіть опцію:\n"
                 "/menu - повернення до головного меню\n"
                 "/message - Відправити повідомлення\n"
                 "/anonymous_message - Відправити анонімне повідомлення\n"
                 "/feedback - зворотній зв'язок для команди\n"
                 )
    bot.send_message(chat_id, menu_text)

def save_feedback_to_csv(feedback_dict: dict) -> None:
    with open(feedback_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            feedback_dict["user_id"],
            feedback_dict["user_name"],
            feedback_dict["user_full_name"],
            feedback_dict["message"],
            dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        ])

def update_user(column, column_change, index, new_status):
    users.loc[users[column] == index, column_change] = new_status
    users.to_csv('users.csv', index=False)

def message_csv(user_id, message_text):
    message_df = pd.read_csv('User_massages.csv')
    message_df = message_df.append({'user_id': user_id, 'message_text': message_text}, ignore_index=True)
    message_df.to_csv('User_massages.csv', index=False)

@bot.message_handler(commands=['add_badword'])
def echo(message) -> None:
    print(message.from_user.id)
    if message.from_user.id == int(admin_id):
        new_word = message.text.replace('/add_badword', '').strip()
        with open("bad_words.txt", 'r') as file:
            words = file.read()
        words += ' ' + new_word
        with open("bad_words.txt", 'w') as file:
            file.write(words)
        bot.reply_to(message, text=f"Word '{new_word}' added to the bad words list.")
    else:
        bot.reply_to(message, text="Не достатній рівень доступу")

@bot.message_handler(commands=["menu"])
def menu(message) -> None:
    user_status[message.from_user.id] = 'menu'
    show_menu(message.chat.id)

@bot.message_handler(commands=["feedback"])
def feedback(message) -> None:
    user_status[message.from_user.id] = "feedback"
    bot.send_message(message.chat.id, "Готові вислуховувати тебе")

@bot.message_handler(commands=["message"])
def message_handler(message) -> None:
    user_status[message.from_user.id] = "message"
    bot.send_message(message.chat.id, "Впишіть текст повідомлення")

@bot.message_handler(commands=["anonymous_message"])
def anonymous_message(message) -> None:
    user_status[message.from_user.id] = "anonymous_message"
    bot.send_message(message.chat.id, "Анонімне повідомлення:")

@bot.message_handler(commands=['start'])
def main(message) -> None:
    user_status[message.from_user.id] = "menu"
    bot.reply_to(message, text=f"Привіт {message.from_user.username}")
    bot.send_message(message.chat.id, text="Цей бот створений для поширення думок без засудження\n")
    show_menu(message.chat.id)

@bot.message_handler(commands=['give_my_info'])
def echo(message) -> None:
    bot.reply_to(message, text=message)

@bot.message_handler(commands=['ban_user'])
def echo(message) -> None:
    if message.from_user.id == int(admin_id):
        bot.reply_to(message, text="Enter user ID")

        @bot.message_handler(func=lambda m: True)
        def get_user_id(m):
            try:
                user_id = int(m.text)
                update_user("user_id", "ban_status", user_id, True)
                bot.reply_to(m, text=f"User {user_id} banned successfully.")
            except ValueError:
                bot.reply_to(m, text="Invalid user ID. Please enter a valid number.")
    else:
        bot.reply_to(message, text="Не достатній рівень доступу")

@bot.message_handler()
def echo(message) -> None:
    current_time = dt.datetime.now()
    last_time = last_message_time.get(message.from_user.id)

    if last_time and (current_time - last_time).total_seconds() < 15:
        remaining_time = 15 - (current_time - last_time).total_seconds()
        bot.reply_to(message, text=f"Please wait {int(remaining_time)} seconds before sending another message.")
        return

    last_message_time[message.from_user.id] = current_time

    if message.from_user.id not in user_status.keys():
        show_menu(message.chat.id)
    elif user_status.get(message.from_user.id) == 'message':
        user_status.pop(message.from_user.id, None)
        if censore(message.text):
            message_csv(message.from_user.id, message.text)
            bot.send_message(chanel_id, f"{message.text}\nвід @{message.from_user.username}")
        else:
            bot.reply_to(message, f"підбирай слова")
        show_menu(message.chat.id)
    elif user_status.get(message.from_user.id) == "anonymous_message":
        user_status.pop(message.from_user.id, None)
        if censore(message.text):
            message_csv(message.from_user.id, message.text)
            bot.send_message(feedback_chanel, f"{message.from_user.id}\n{message.text}\n")
            bot.send_message(chanel_id, f"{message.text}\nвід анонімного користувача")
        else:
            bot.reply_to(message, f"підбирай слова")
        show_menu(message.chat.id)
    elif user_status.get(message.from_user.id) == "feedback":
        feedback = {
            "message": message.text,
            "user_id": message.from_user.id,
            "user_name": message.from_user.username,
            "user_full_name": message.from_user.first_name + " " + (message.from_user.last_name or "")
        }
        bot.send_message(feedback_chanel, text=f"{feedback['user_id']}\n"
                                               f"{feedback['user_name']}\n"
                                               f"{feedback['user_full_name']}, "
                                               f"{feedback['message']}")
        save_feedback_to_csv(feedback)
        bot.reply_to(message, "Дякуємо за ваш відгук!")
        user_status[message.from_user.id] = "menu"
        show_menu(message.chat.id)

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(15)

if __name__ == "__main__":
    run_bot()
