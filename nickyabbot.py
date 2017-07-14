import sqlite3
import os
import telebot


def db_setup(dbfile='troll.db'):
    db = sqlite3.connect(dbfile)
    cursor = db.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS quotes (chatid int, quote text)')
    cursor.execute('DELETE FROM quotes WHERE chatid = 0')
    with open('staticquotes.txt', 'r') as staticquotes:
        for line in staticquotes:
            cursor.execute('''INSERT INTO quotes(chatid,quote) VALUES(?,?)''', (0, line))
    db.commit()
    db.close()


if 'TOKEN' not in os.environ:
    print("missing TOKEN.Leaving...")
    os._exit(1)

bot = telebot.TeleBot(os.environ['TOKEN'])


@bot.message_handler(commands=['troll'])
def random(message):
    chatid = message.chat.id if message.chat.title is not None else 0
    db = sqlite3.connect('troll.db')
    cursor = db.cursor()
    cursor.execute('''SELECT quote FROM quotes WHERE chatid = ? OR chatid = 0 ORDER BY RANDOM() LIMIT 1''', (chatid,))
    randomquote = cursor.fetchone()[0]
    db.close()
    print("Sending Troll message...")
    bot.reply_to(message, randomquote)


@bot.message_handler(commands=['trolladd'])
def add(message):
    quote = message.text.replace('/trolladd ', '')
    if quote == '':
        bot.reply_to(message, 'Missing Troll text to add')
        return
    if message.chat.title is None:
        bot.reply_to(message, 'Trolls can only be added to channels')
        return
    db = sqlite3.connect('troll.db')
    cursor = db.cursor()
    cursor.execute('''INSERT INTO quotes(chatid,quote) VALUES(?,?)''', (message.chat.id, quote))
    print("Adding Troll message to chat %s" % message.chat.title)
    bot.reply_to(message, 'Troll added to your channel')
    cursor.execute('''SELECT * FROM quotes''')
    allrows = cursor.fetchall()
    for q in allrows:
        print q
    db.commit()
    db.close()

db_setup(dbfile='troll.db')
print("Ready for trolling!")
bot.polling()
