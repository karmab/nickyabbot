# import logging
import sqlite3
import os
import re
import random
import requests
import string
import telebot
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

emojis = re.compile(u"(\ud83d[\ude00-\ude4f])|"  # emoticons
                    u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
                    u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
                    u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
                    u"(\ud83c[\udde0-\uddff])"  # flags (iOS)
                    "+", flags=re.UNICODE)


def db_setup(dbpath='/tmp/troll'):
    if not os.path.exists(dbpath):
        os.makedirs(dbpath)
    db = sqlite3.connect("%s/db" % dbpath)
    cursor = db.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS quotes (chatid int, keyword text not null, quote text not null)')
    cursor.execute('CREATE TABLE IF NOT EXISTS levels (chatid int, level int)')
    db.commit()
    db.close()


def random_gif(key, search):
    r = requests.get("http://api.giphy.com/v1/gifs/random?tag=%s&api_key=%s" % (search, key))
    if 'data' in r.json():
        return r.json()['data']['image_url']


if 'TOKEN' not in os.environ:
    print("missing TOKEN.Leaving...")
    os._exit(1)
token = os.environ.get('TOKEN')

if 'GIPHYKEY' not in os.environ:
    print("missing GIPHYKEY.Leaving...")
    os._exit(1)
giphykey = os.environ.get('GIPHYKEY')

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
            if len(quote.split(' ')) == 1 and len(quote) >= 30:
                quote = 'MEDIA'
            quotes = '%s%s -> %s\n' % (quotes, keyword, quote)
        bot.reply_to(message, quotes)


@bot.message_handler(commands=["trolladd", "trolladd%s" % botname])
def trolladd(message):
    if 'group' not in message.chat.type:
        bot.reply_to(message, 'Trolls can only be added to groups')
        return
    bot.send_message(message.chat.id, "Allright @%s. Give me a keyword. Put $ at the end for a rhyme" % message.from_user.username, reply_markup=telebot.types.ForceReply(selective=True))
    return


@bot.message_handler(commands=["trolldelete", "trolldelete%s" % botname])
def trolldelete(message):
    trolldb = '/tmp/troll/db'
    if 'group' not in message.chat.type:
        bot.reply_to(message, 'Trolls can only be deleted from groups')
        return
    db = sqlite3.connect(trolldb)
    cursor = db.cursor()
    cursor.execute('''SELECT keyword,quote FROM quotes where chatid = ? ORDER BY keyword''', (message.chat.id,))
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
@bot.message_handler(content_types=['audio'])
@bot.message_handler(content_types=['photo'])
@bot.message_handler(content_types=['voice'])
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
                    if keyword[-1] == '$' and (len(quote) < 4 or quote[-4:] != keyword[-5:-1]):
                        markup = telebot.types.ReplyKeyboardHide(selective=True)
                        print("Invalid format for this rhyme")
                        bot.reply_to(message, 'Invalid format for this rhyme', reply_markup=markup)
                        return
                elif message.sticker is not None:
                    quote = message.sticker.file_id
                elif message.document is not None:
                    quote = message.document.file_id
                elif message.photo is not None:
                    quote = message.photo[0].file_id
                elif message.audio is not None:
                    quote = message.audio.file_id
                elif message.voice is not None:
                    quote = message.voice.file_id
                else:
                    print("Invalid format for this quote")
                    markup = telebot.types.ReplyKeyboardHide(selective=True)
                    bot.reply_to(message, 'Invalid format for this quote', reply_markup=markup)
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
                if len(text.strip().split(' ')) > 1 or len(text.strip()) == 1:
                    bot.send_message(message.chat.id, "Wrong @%s. I needed a single word" % message.from_user.username)
                elif text[-1] == '$' and len(text) < 5:
                    bot.send_message(message.chat.id, "Wrong @%s. You need at least 5 characters for a rhyme" % message.from_user.username)
                else:
                    if text[-1] == '$':
                        keywords[message.from_user.username] = text.lower()
                    else:
                        keywords[message.from_user.username] = text.strip().lower()
                    bot.send_message(message.chat.id, "Allright @%s. Give me a troll. you can also use randomgif or randomgif KEYWORD" % message.from_user.username, reply_markup=telebot.types.ForceReply(selective=True))
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
            words = []
            for t in message.text.lower().split(' '):
                if not t.endswith('++' or '--'):
                    for c in string.punctuation:
                        t = t.replace(c, '')
                t = emojis.sub(r'', t)
                words.append(t)
            cursor.execute('''SELECT level FROM levels where chatid = ?''', (message.chat.id,))
            result = cursor.fetchone()
            level = int(result[0]) if result is not None else LEVEL
            if random.randint(1, 5) not in range(1, level + 1) or level == 0:
                print("NOT HIT")
                return
            for index, word in enumerate(words):
                if index == len(words) - 1 and "%s$" % word in quotekeys:
                    word = "%s$" % word
                if word.strip().lower() in quotekeys:
                    cursor.execute('''SELECT quote FROM quotes where chatid = ? AND keyword = ? ORDER BY RANDOM() LIMIT 1''', (message.chat.id, word))
                    quote = cursor.fetchone()
                    if 'randomgif' in quote[0].lower():
                        search = quote[0].split(' ')[1] if len(quote[0].split(' ')) == 2 else word
                        url = random_gif(giphykey, search)
                        if url is not None:
                            bot.send_document(message.chat.id, url)
                    elif len(quote[0].split(' ')) == 1:
                        fileid = quote[0]
                        try:
                            bot.send_sticker(message.chat.id, fileid)
                        except:
                            try:
                                bot.send_document(message.chat.id, fileid)
                            except:
                                try:
                                    bot.send_audio(message.chat.id, fileid)
                                except:
                                    try:
                                        bot.send_voice(message.chat.id, fileid)
                                    except:
                                        bot.send_photo(message.chat.id, fileid)
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
