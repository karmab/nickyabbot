# import logging
import sqlite3
import os
import re
import telebot
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def db_setup(dbfile='troll.db'):
    db = sqlite3.connect(dbfile)
    cursor = db.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS quotes (chatid int, quote text)')
    cursor.execute('DELETE FROM quotes WHERE chatid = 0')
    with open(os.path.expanduser('~/staticquotes.txt'), 'r') as staticquotes:
        for line in staticquotes:
            cursor.execute('''INSERT INTO quotes(chatid,quote) VALUES(?,?)''', (0, line.strip()))
    db.commit()
    db.close()


if 'TOKEN' not in os.environ:
    print("missing TOKEN.Leaving...")
    os._exit(1)

# logger = telebot.logger
# telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot(os.environ['TOKEN'])
botname = "@%s" % bot.get_me().username


@bot.message_handler(commands=['start', "start%s" % botname])
def start(message):
    startmessage = ''' *Welcome to the troll bot*

This bot is designed to ease trolling within your group chats

/troll to get a random troll
/troll PATTERN to get matching troll
/trolladd PATTERN to add troll to current group
/trolldelete PATTERN to delete troll from current group
'''
    bot.reply_to(message, startmessage, parse_mode='Markdown')


@bot.message_handler(commands=['trollhelp', 'help', "help%s" % botname])
def help(message):
    helpmessage = '''Those are the commands available:
/troll - Displays random or matching troll
/trolladd - Adds indicated troll
/trolldelete - Deletes given troll
/trolllist - Lists all trolls
/trollhelp - This help
'''
    bot.reply_to(message, helpmessage)


@bot.message_handler(commands=['troll', "troll%s" % botname])
def get(message):
    global trolldb
    quote = re.sub(r"/troll(%s|)" % botname, '', message.text).strip()
    chatid = message.chat.id if message.chat.title is not None else 0
    db = sqlite3.connect(trolldb)
    cursor = db.cursor()
    if quote == '':
        cursor.execute('''SELECT quote FROM quotes WHERE chatid = ? OR chatid = 0 ORDER BY RANDOM() LIMIT 1''', (chatid,))
        fetch = cursor.fetchone()
    else:
        cursor.execute("SELECT quote FROM quotes WHERE quote like ? AND (chatid = ? OR chatid = 0) ORDER BY RANDOM() LIMIT 1", ('%' + quote + '%', chatid,))
        fetch = cursor.fetchone()
        if fetch is None:
            print("No Matching quote found")
            bot.reply_to(message, 'No Matching quote found')
            return
    quote = fetch[0]
    db.close()
    print("Sending troll message to user %s" % message.from_user.username)
    bot.reply_to(message, quote)


@bot.message_handler(commands=['trollall', 'trolllist', "trollall%s" % botname, "trolllist%s" % botname])
def all(message):
    global trolldb
    db = sqlite3.connect(trolldb)
    cursor = db.cursor()
    if 'group' in message.chat.type:
        cursor.execute('SELECT quote FROM quotes where chatid = ? or chatid = 0', (message.chat.id,))
    else:
        cursor.execute('SELECT quote FROM quotes where chatid = 0')
    quotes = '\n'.join([q[0] for q in cursor.fetchall()])
    db.close()
    print("Sending all troll messages to user %s" % message.from_user.username)
    bot.reply_to(message, quotes)


@bot.inline_handler(lambda query: query.query == 'text')
def inline_all(query):
    message = query.query
    global trolldb
    chatid = 0
    db = sqlite3.connect(trolldb)
    cursor = db.cursor()
    cursor.execute("SELECT quote FROM quotes WHERE quote like ? AND (chatid = ? OR chatid = 0)", ('%' + message + '%', chatid,))
    fetch = cursor.fetchone()
    if fetch is None:
        print("No Matching quote found")
        bot.answer_inline_query(query.id, 'Nothing found')
        return
    results = []
    for index, value in enumerate(fetch):
        results.append(telebot.types.InlineQueryResultArticle(str(index), value, telebot.types.InputTextMessageContent("<troll>%s</troll>" % value)))
    print("Sending all troll messages to user %s" % query.from_user.username)
    bot.answer_inline_query(query.id, results)


@bot.message_handler(commands=['trolladd', "trolladd%s" % botname])
def add(message):
    global trolldb
    if 'group' not in message.chat.type:
        bot.reply_to(message, 'Trolls can only be added to groups')
        return
    quote = re.sub(r"/trolladd(%s|)" % botname, '', message.text).strip()
    if quote == '':
        # bot.reply_to(message, 'Missing troll text to add')
        bot.send_message(message.chat.id, "Allright. Give me a troll", reply_markup=telebot.types.ForceReply(selective=False))
        return
    quote = quote.strip()
    db = sqlite3.connect(trolldb)
    cursor = db.cursor()
    cursor.execute('''SELECT quote FROM quotes where chatid = ? AND quote == ?''', (message.chat.id, quote))
    existing = cursor.fetchone()
    if existing is not None:
        bot.reply_to(message, 'Troll allready exists in this group')
        return
    cursor.execute('''INSERT INTO quotes(chatid,quote) VALUES(?,?)''', (message.chat.id, quote))
    print("Adding Troll message to group %s" % message.chat.title)
    bot.reply_to(message, 'Troll added to your group')
    db.commit()
    db.close()


@bot.message_handler(commands=['trolldel', 'trolldelete', "trolldel%s" % botname, "trolldelete%s" % botname])
def delete(message):
    global trolldb
    quote = re.sub(r"/troll(delete|del)(%s|)" % botname, '', message.text).strip()
    print quote
    if quote == '':
        bot.reply_to(message, 'Missing troll text to delete')
        return
    if 'group' not in message.chat.type:
        bot.reply_to(message, 'Trolls can only be deleted from groups')
        return
    db = sqlite3.connect(trolldb)
    cursor = db.cursor()
    deleted = cursor.execute('''DELETE FROM QUOTES WHERE chatid = ? and  quote = ?''', (message.chat.id, quote))
    if deleted.rowcount > 0:
        print("Deleted Troll message from group %s" % message.chat.title)
        bot.reply_to(message, 'Troll deleted from your group')
    else:
        print("No Troll message deleted from group %s" % message.chat.title)
        bot.reply_to(message, 'Troll was not deleted from your group')
    db.commit()
    db.close()


@bot.message_handler(func=lambda m: True)
def custom(message):
    if 'transcoding' in message.text.lower():
        bot.reply_to(message, 'un chupito para @%s!!!' % message.from_user.username)
    elif '$deity' in message.text.lower():
        bot.reply_to(message, '$deity no existe @%s. Lo siento...' % message.from_user.username)
    elif message.reply_to_message is not None and message.reply_to_message.text is not None and 'Give me a troll' in message.reply_to_message.text:
        quote = message.text.strip()
        db = sqlite3.connect(trolldb)
        cursor = db.cursor()
        cursor.execute('''SELECT quote FROM quotes where chatid = ? AND quote == ?''', (message.chat.id, quote))
        existing = cursor.fetchone()
        if existing is not None:
            bot.reply_to(message, 'Troll allready exists in this group')
            return
        cursor.execute('''INSERT INTO quotes(chatid,quote) VALUES(?,?)''', (message.chat.id, quote))
        print("Adding Troll message to group %s" % message.chat.title)
        bot.reply_to(message, 'Troll added to your group')
        db.commit()
        db.close()


trolldb = os.path.expanduser("~/troll.db")
db_setup(dbfile=trolldb)
print("Ready for trolling!")
bot.polling()
