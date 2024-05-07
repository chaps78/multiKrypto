import telebot
import json

with open('bin_key.json') as json_file:
    config = json.load(json_file)

TELEG_TOKEN = config["telegram_token"]
#Id du chat pour le BOT telegram
BOT_CHAT_ID = config["chat_id"]
bot = telebot.TeleBot(TELEG_TOKEN)
bot.send_message(BOT_CHAT_ID, "Bonjour")


class teleAcces():
    def send_message(self,message):
        bot = telebot.TeleBot(TELEG_TOKEN)
        bot.send_message(BOT_CHAT_ID, message)

def main():
    tele = teleAcces()
    tele.send_message("haaaaaa")

if __name__ == '__main__':
     main()