# import logging
import sqlite3
import os
import random
import telebot
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def db_setup(dbpath='/tmp/troll'):
    if not os.path.exists(dbpath):
        os.makedirs(dbpath)
    db = sqlite3.connect("%s/db" % dbpath)
    cursor = db.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS quotes (chatid int, keyword text not null, quote text not null)')
    cursor.execute('CREATE TABLE IF NOT EXISTS levels (chatid int, level int)')
    db.commit()
    db.close()


if 'TOKEN' not in os.environ:
    print("missing TOKEN.Leaving...")
    os._exit(1)
token = os.environ.get('TOKEN')

bot = telebot.TeleBot(token)
bot.skip_pending = True
botname = "@%s" % bot.get_me().username


@bot.message_handler(commands=["start", "start%s" % botname])
def start(message):
    startmessage = ''' *Welcome to the troll bot*

This bot is designed to ease trolling within your group chats

/trolladd add troll to current group
/trolldelete delete troll from current group
/trolllevel show randomness
/trolllist list all the trolls from current group
/trollset ajust randomness
/help this help
'''
    bot.reply_to(message, startmessage, parse_mode='Markdown')


@bot.message_handler(commands=["help", "help%s" % botname])
def help(message):
    helpmessage = '''Those are the commands available:
/trolladd add troll to current group
/trolldelete delete troll from current group
/trolllevel show randomness
/trolllist list all the trolls from current group
/trollset ajust randomness
/help this help
'''
    bot.reply_to(message, helpmessage)


@bot.message_handler(commands=["trollset", "trollset%s" % botname])
def trollset(message):
    if 'group' not in message.chat.type:
        bot.reply_to(message, 'Troll settings only apply to groups')
        return
    markup = telebot.types.ReplyKeyboardMarkup(row_width=1, selective=True)
    for entry in range(0, 6):
        markup.add(telebot.types.KeyboardButton(str(entry)))
    bot.send_message(message.chat.id, "Allright @%s. Pick level of activity" % message.from_user.username, reply_markup=markup)
    return


@bot.message_handler(commands=["trolllevel", "trolllevel%s" % botname])
def trolllevel(message):
    trolldb = '/tmp/troll/db'
    db = sqlite3.connect(trolldb)
    cursor = db.cursor()
    if 'group' in message.chat.type:
        cursor.execute('SELECT level FROM levels where chatid = ?', (message.chat.id,))
    result = cursor.fetchone()
    level = int(result[0]) if result is not None else LEVEL
    db.close()
    print("Sending troll level to user %s" % message.from_user.username)
    bot.reply_to(message, "Troll level of this group is %s/5" % level)


@bot.message_handler(commands=["trolllist", "trolllist%s" % botname])
def trolllist(message):
    trolldb = '/tmp/troll/db'
    db = sqlite3.connect(trolldb)
    cursor = db.cursor()
    if 'group' not in message.chat.type:
        bot.reply_to(message, "No quotes available outside of groups")
        return
    cursor.execute('SELECT keyword,quote FROM quotes where chatid = ? ORDER BY keyword', (message.chat.id,))
    results = cursor.fetchall()
    db.close()
    print("Sending all troll messages to user %s" % message.from_user.username)
    if not results:
        bot.reply_to(message, "No quotes found")
    else:
        quotes = ''
        for q in results:
            keyword, quote = q[0], q[1]
            if len(quote) == 31:
                quote = 'FOTO/STICKER'
            quotes = '%s%s -> %s\n' % (quotes, keyword, quote)
        bot.reply_to(message, quotes)


@bot.message_handler(commands=["trolladd", "trolladd%s" % botname])
def trolladd(message):
    if 'group' not in message.chat.type:
        bot.reply_to(message, 'Trolls can only be added to groups')
        return
    bot.send_message(message.chat.id, "Allright @%s. Give me a keyword" % message.from_user.username, reply_markup=telebot.types.ForceReply(selective=True))
    return


@bot.message_handler(commands=["trolldelete", "trolldelete%s" % botname])
def trolldelete(message):
    trolldb = '/tmp/troll/db'
    if 'group' not in message.chat.type:
        bot.reply_to(message, 'Trolls can only be deleted from groups')
        return
    db = sqlite3.connect(trolldb)
    cursor = db.cursor()
    cursor.execute('''SELECT keyword,quote FROM quotes where chatid = ?''', (message.chat.id,))
    existing = cursor.fetchall()
    db.close()
    if not existing:
        bot.reply_to(message, 'No trolls for you to delete')
    else:
        markup = telebot.types.ReplyKeyboardMarkup(row_width=1, selective=True)
        for entry in existing:
            markup.add(telebot.types.KeyboardButton("%s -> %s" % (entry[0], entry[1])))
        bot.send_message(message.chat.id, "Allright @%s. Delete a troll" % message.from_user.username, reply_markup=markup)
    return


@bot.message_handler(func=lambda m: True)
@bot.message_handler(content_types=['sticker'])
@bot.message_handler(content_types=['document'])
def custom(message):
    trolldb = '/tmp/troll/db'
    db = sqlite3.connect(trolldb)
    cursor = db.cursor()
    try:
        if message.reply_to_message is not None and message.reply_to_message.text is not None:
            if 'Pick level of activity' in message.reply_to_message.text:
                level = int(message.text.strip())
                db = sqlite3.connect(trolldb)
                cursor = db.cursor()
                cursor.execute('''DELETE FROM levels where chatid = ?''', (message.chat.id,))
                cursor.execute('''INSERT INTO levels(chatid,level) VALUES(?,?)''', (message.chat.id, level))
                print("Troll level set for group %s" % message.chat.title)
                markup = telebot.types.ReplyKeyboardHide(selective=True)
                bot.reply_to(message, 'Troll level set for your group', reply_markup=markup)
                db.commit()
                db.close()
            elif 'Give me a troll' in message.reply_to_message.text:
                keyword = keywords[message.from_user.username]
                if message.text is not None:
                    quote = message.text.strip()
                elif message.sticker is not None:
                    quote = message.sticker.file_id
                elif message.document is not None:
                    quote = message.document.file_id
                else:
                    print("Invalid format for this quote")
                    bot.reply_to(message, 'Invalid format for this quote')
                    return
                db = sqlite3.connect(trolldb)
                cursor = db.cursor()
                cursor.execute('''SELECT quote FROM quotes where chatid = ? AND quote = ? AND keyword = ?''', (message.chat.id, quote, keyword))
                results = cursor.fetchall()
                if results:
                    print("Quote already exists for this keyword")
                    bot.reply_to(message, 'Quote already exists for this keyword')
                else:
                    cursor.execute('''INSERT INTO quotes(chatid,keyword,quote) VALUES(?,?,?)''', (message.chat.id, keyword, quote))
                    print("Adding Troll to group %s" % message.chat.title)
                    bot.reply_to(message, 'Troll added to your group')
                db.commit()
                db.close()
            elif 'Give me a keyword' in message.reply_to_message.text:
                text = message.text
                if text is None:
                    bot.send_message(message.chat.id, "Wrong @%s. I needed a single word" % message.from_user.username)
                    return
                keyword = text.strip()
                if len(keyword.split(' ')) > 1 or len(keyword) == 1:
                    bot.send_message(message.chat.id, "Wrong @%s. I needed a single word" % message.from_user.username)
                else:
                    keywords[message.from_user.username] = keyword
                    bot.send_message(message.chat.id, "Allright @%s. Give me a troll" % message.from_user.username, reply_markup=telebot.types.ForceReply(selective=True))
            elif 'Delete a troll' in message.reply_to_message.text:
                keyword = message.text.strip().split('->')[0].strip()
                quote = message.text.strip().split('->')[1].strip()
                db = sqlite3.connect(trolldb)
                cursor = db.cursor()
                deleted = cursor.execute('''DELETE FROM quotes WHERE chatid = ? AND keyword = ? AND quote = ?''', (message.chat.id, keyword, quote))
                if deleted.rowcount > 0:
                    print("Deleted Troll from group %s" % message.chat.title)
                    markup = telebot.types.ReplyKeyboardHide(selective=True)
                    bot.reply_to(message, 'Troll deleted from your group', reply_markup=markup)
                else:
                    bot.reply_to(message, 'No troll found to delete')
                db.commit()
                db.close()
        elif message.text is None:
            return
        else:
            cursor.execute('''SELECT keyword FROM quotes where chatid = ?''', (message.chat.id,))
            quotekeys = [r[0] for r in cursor.fetchall()]
            words = message.text.lower().split(' ')
            cursor.execute('''SELECT level FROM levels where chatid = ?''', (message.chat.id,))
            result = cursor.fetchone()
            level = int(result[0]) if result is not None else LEVEL
            if random.randint(1, 5) not in range(1, level + 1) or level == 0:
                print("NOT HIT")
                return
            for word in words:
                if word in quotekeys:
                    cursor.execute('''SELECT quote FROM quotes where chatid = ? AND keyword = ? ORDER BY RANDOM() LIMIT 1''', (message.chat.id, word))
                    quote = cursor.fetchone()
                    if len(quote[0].split(' ')) == 1 and len(quote[0].split(' ')[0]) == 31:
                        fileid = quote[0].split(' ')[0]
                        try:
                            bot.send_sticker(message.chat.id, fileid)
                        except:
                            bot.send_document(message.chat.id, fileid)
                    else:
                        bot.reply_to(message, quote)
                    break
            db.close()
    except Exception as e:
        print(e)


db_setup(dbpath='/tmp/troll')
print("Ready for trolling!")
LEVEL = 3
keywords = {}
bot.polling()
