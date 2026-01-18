#all commmands listed below 
# /start - welcome message
# /alive - check if bot is alive
# /id - get user ID
# /whoami - check if user is admin or regular user
# /ping - check if user is moderator or not
# /ban - ban a user (moderator only)
# /unban - unban a user (moderator only)
# /warn - warn a user (moderator only)
# /clearwarns - clear warnings for a user (moderator only)
# /mute - mute a user for a specified duration (moderator only)
# /unmute - unmute a user (moderator only)
# /warnings - check warnings for a user (moderator only)
# /sticker - send a predefined sticker

from dotenv import load_dotenv
import os
import telebot
import time
from telebot import types

load_dotenv()  # automatically reads .env

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

warnings = {}
MAX_WARNINGS = 3

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am your friendly moderation bot.")


@bot.message_handler(commands=[ 'alive'])
def alive(message):
    bot.reply_to(message, "yeaah i am alive !!!!!!!!!!")

@bot.message_handler(commands=['id'])
def fetch_id(msg):
    if msg.reply_to_message:
        uid = msg.reply_to_message.from_user.id
        bot.reply_to(msg, f"User ID: {uid}")
    else:
        bot.reply_to(msg, f"Your ID: {msg.from_user.id}")
# Helper function to check if the user is the admin
def is_owner(msg):
    return msg.from_user.id == ADMIN_ID


@bot.message_handler(commands=['whoami'])
def whoami(msg):
    if is_owner(msg):
        bot.reply_to(msg, "You are the omnipotent admin")
    else:
        bot.reply_to(msg, "You are just a filthy user")
# Helper function to check if a user is an admin in a group
def is_group_admin(bot, chat_id, user_id):
    admins = bot.get_chat_administrators(chat_id)
    return any(a.user.id == user_id for a in admins)

# Helper function to check if a user can moderate (is admin or owner)
def can_moderate(bot, msg):
    if msg.from_user.id == ADMIN_ID:
        return True

    if msg.chat.type in ["group", "supergroup"]:
        return is_group_admin(bot, msg.chat.id, msg.from_user.id)

    return False

# Command that requires moderator access ( admin or owner)
# this command replies with a confirmation message if the user has moderator access
@bot.message_handler(commands=['ping'])
def ping(msg):
    if not can_moderate(bot, msg):
        return

    bot.reply_to(msg, "YESS DADDY U CAN BANG ME !!!!!")

# Command to ban a user ( moderator only)
@bot.message_handler(commands=['ban'])
def ban_user(msg):
    # only in groups
    if msg.chat.type not in ["group", "supergroup"]:
        return

    # permission check
    if not can_moderate(bot, msg):
        return

    # must reply to someone
    if not msg.reply_to_message:
        return

    target = msg.reply_to_message.from_user

    # safety checks
    if target.id == msg.from_user.id:
        return  # can't ban yourself

    if target.id == ADMIN_ID:
        return  # can't ban owner

    try:
        bot.ban_chat_member(msg.chat.id, target.id)
        bot.reply_to(
            msg,
            f"🚫 Banned: {target.first_name} ({target.id})"
        )
    except Exception:
        pass

# Command to unban a user ( moderator only)
@bot.message_handler(commands=['unban'])
def unban_user(msg):
    # only groups
    if msg.chat.type not in ["group", "supergroup"]:
        return

    # permission check
    if not can_moderate(bot, msg):
        return

    parts = msg.text.split()
    if len(parts) != 2:
        return  # no ID provided

    try:
        user_id = int(parts[1])
    except ValueError:
        return  # invalid ID

    try:
        bot.unban_chat_member(msg.chat.id, user_id)
        bot.reply_to(msg, f"✅ Unbanned user {user_id}")
    except Exception:
        pass

# Command to warn a user ( moderator only)
@bot.message_handler(commands=['warn'])
def warn_user(msg):
    # group only
    if msg.chat.type not in ["group", "supergroup"]:
        return

    # permission check
    if not can_moderate(bot, msg):
        return

    # must reply
    if not msg.reply_to_message:
        return

    target = msg.reply_to_message.from_user

    # safety checks
    if target.id == msg.from_user.id:
        return

    if target.id == ADMIN_ID:
        return

    key = (msg.chat.id, target.id)
    warnings[key] = warnings.get(key, 0) + 1

    count = warnings[key]

    if count >= MAX_WARNINGS:
        try:
            bot.ban_chat_member(msg.chat.id, target.id)
            bot.reply_to(
                msg,
                f"🚫 {target.first_name} banned ({count}/{MAX_WARNINGS} warnings)"
            )
            del warnings[key]
        except Exception:
            pass
    else:
        bot.reply_to(
            msg,
            f"⚠️ Warning {count}/{MAX_WARNINGS} for {target.first_name}"
        )

# Command to clear warnings for a user ( moderator only)
@bot.message_handler(commands=['clearwarns'])
def clear_warns(msg):
    # group only
    if msg.chat.type not in ["group", "supergroup"]:
        return

    # permission check
    if not can_moderate(bot, msg):
        return

    # must reply
    if not msg.reply_to_message:
        return

    target = msg.reply_to_message.from_user
    key = (msg.chat.id, target.id)

    if key in warnings:
        del warnings[key]
        bot.reply_to(
            msg,
            f"🧹 Warnings cleared for {target.first_name}"
        )
    else:
        bot.reply_to(
            msg,
            f"ℹ️ {target.first_name} has no warnings"
        )
# Helper function to parse duration strings like '10m', '2h', '1d'
def parse_duration(text):
    try:
        value = int(text[:-1])
        unit = text[-1]

        if unit == 'm':
            return value * 60
        if unit == 'h':
            return value * 3600
        if unit == 'd':
            return value * 86400
    except Exception:
        pass

    return None



# Command to mute a user for 10 minutes ( moderator only)

@bot.message_handler(commands=['mute'])
def mute_user(msg):
    if msg.chat.type not in ["group", "supergroup"]:
        return

    if not can_moderate(bot, msg):
        return

    if not msg.reply_to_message:
        return

    target = msg.reply_to_message.from_user

    if target.id == msg.from_user.id:
        return

    if target.id == ADMIN_ID:
        return

    # default: 10 minutes
    seconds = 10 * 60

    parts = msg.text.split()
    if len(parts) == 2:
        parsed = parse_duration(parts[1])
        if parsed:
            seconds = parsed

    until_date = int(time.time()) + seconds

    permissions = types.ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )

    try:
        bot.restrict_chat_member(
            msg.chat.id,
            target.id,
            permissions=permissions,
            until_date=until_date
        )

        bot.reply_to(
            msg,
            f"🔇 Muted {target.first_name} for {seconds // 60} minutes"
        )
    except Exception:
        pass

# Command to unmute a user ( moderator only)

@bot.message_handler(commands=['unmute'])
def unmute_user(msg):
    # group only
    if msg.chat.type not in ["group", "supergroup"]:
        return

    # permission check
    if not can_moderate(bot, msg):
        return

    # must reply
    if not msg.reply_to_message:
        return

    target = msg.reply_to_message.from_user

    # safety
    if target.id == ADMIN_ID:
        return

    permissions = types.ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )

    try:
        bot.restrict_chat_member(
            msg.chat.id,
            target.id,
            permissions=permissions
        )
        bot.reply_to(
            msg,
            f"🔊 Unmuted {target.first_name}"
        )
    except Exception:
        pass
# Command to check warnings for a user ( moderator only)
@bot.message_handler(commands=['warnings'])
def check_warnings(msg):
    # group only
    if msg.chat.type not in ["group", "supergroup"]:
        return

    # permission check
    if not can_moderate(bot, msg):
        return

    # decide target
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
    else:
        target = msg.from_user

    key = (msg.chat.id, target.id)
    count = warnings.get(key, 0)

    bot.reply_to(
        msg,
        f"⚠️ Warnings for {target.first_name}: {count}/{MAX_WARNINGS}"
    )

# Command to send a sticker
STICKER_ID = "CAACAgUAAyEFAATMbkDHAAMhaWw7tqBC9qpcCCfOSrLEhWRTWRQAAtAVAAKRZVBUFIEXEuL8MUs4BA"

@bot.message_handler(commands=['sticker'])
def send_sticker(msg):
    bot.send_sticker(msg.chat.id, STICKER_ID)
# Keep the bot running
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

def run_server():
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()


bot.infinity_polling()
