import telebot as tb
import datetime as dt
import json
import csv
import re
import time

tb.apihelper.Timeout = 24*60*60

config = json.load(open('config.json'))
bot = tb.TeleBot(config.get('bot'))
chanel_id = config.get('chanel_id')
feedback_path = config.get('feedback_path')
user_status = {}
print(user_status)


with open("bad_words.txt", 'r', encoding='utf-8') as file:
    bad_words = {word.strip().lower() for word in file}


def censore(text: str) -> bool:
    text = re.sub(r'[^\w\s]', '', text)
    words = text.lower().split()

    for word in words:
        if word in bad_words:
            return False
    return True


def show_menu(chat_id: int) -> None:
    menu_text = (
        "Виберіть опцію:\n"
        "/menu - повернення до головного меню\n"
        "/message - Відправити повідомлення\n"
        "/anonymous_message - Відправити анонімне повідомлення\n"
        "/feedback - зворотній зв'язок для команди\n"
    )
    bot.send_message(chat_id, menu_text)


def save_feedback_to_csv(feedback: dict) -> None:
    with open(feedback_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            feedback["user_id"],
            feedback["user_name"],
            feedback["user_full_name"],
            feedback["message"],
            dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        ])


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


@bot.message_handler()
def echo(message) -> None:
    if not message.from_user.id in user_status.keys():
        show_menu(message.chat.id)
    elif user_status.get(message.from_user.id) == 'message':
        user_status.pop(message.from_user.id, None)
        if censore(message.text):
            bot.send_message(chanel_id, f"{message.text}\nвід @{message.from_user.username}")
        else:
            bot.reply_to(message, f"підбирай слова")
        show_menu(message.chat.id)
    elif user_status.get(message.from_user.id) == "anonymous_message":
        user_status.pop(message.from_user.id, None)
        if censore(message.text):
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
