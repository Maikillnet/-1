
import os
import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)

TOKEN = "8053119583:AAEk2_DTDRqta2_gPuZ83DZkcebwyZ1nKPM"
CHANNEL_ID = "@politbyrg"
BOT_PASSWORD = "Mailmail20020921"
AUTHORIZED_USERS = set()
AUTHORIZED_FILE = "authorized_users.txt"
BANNED_WORDS = [
    "хуй", "пизда", "ебать", "блядь", "мразь", "сука", "гандон", "даун", "чмо", "уебище",
    "идиот", "тварь", "сволочь", "жопа", "говно", "мудак", "педик", "гей", "долбаёб", "шалава",
    "проститутка", "аутист", "дебил", "кретин", "урод", "негр", "нацист", "расист", "еблан",
    "петух", "лох", "извращенец", "обоссышься", "дрянь", "ссанина", "курва", "шлюха", "ебанат", "выблядок"
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
application = ApplicationBuilder().token(TOKEN).build()

def load_authorized():
    if os.path.exists(AUTHORIZED_FILE):
        with open(AUTHORIZED_FILE, "r") as f:
            for line in f:
                AUTHORIZED_USERS.add(int(line.strip()))

def save_authorized():
    with open(AUTHORIZED_FILE, "w") as f:
        for uid in AUTHORIZED_USERS:
            f.write(str(uid) + "\n")

load_authorized()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in AUTHORIZED_USERS:
        await update.message.reply_text("✅ Вы уже авторизованы.")
        return

    if context.args and context.args[0] == BOT_PASSWORD:
        AUTHORIZED_USERS.add(uid)
        save_authorized()
        await update.message.reply_text("✅ Доступ подтверждён.")
    else:
        await update.message.reply_text("🔒 Введите пароль: /start <пароль>")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    await update.message.reply_text(
        "/start <пароль> — авторизация\n"
        "/help — список команд\n"
        "/post <минуты> <текст> — отложенный пост\n"
        "/broadcast <текст> — рассылка\n"
        "/exit — выйти\n"
        "/stats — пользователи\n"
        "/channelstats — канал\n"
        "/lastposts — последние посты"
    )

async def post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in AUTHORIZED_USERS: return
    msg = update.message
    caption = msg.caption if msg.caption else msg.text
    if not caption: return await msg.reply_text("⚠️ Формат: /post <минуты> <текст>")
    try:
        minutes, text = int(caption.split()[1]), " ".join(caption.split()[2:])
    except:
        return await msg.reply_text("⚠️ Формат: /post <минуты> <текст>")
    await msg.reply_text(f"Сообщение будет отправлено через {minutes} минут.")
    await asyncio.sleep(minutes * 60)
    if msg.photo:
        await bot.send_photo(CHANNEL_ID, msg.photo[-1].file_id, caption=text)
    elif msg.video:
        await bot.send_video(CHANNEL_ID, msg.video.file_id, caption=text)
    else:
        await bot.send_message(CHANNEL_ID, text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    text = " ".join(context.args)
    if not text: return await update.message.reply_text("⚠️ Введите текст рассылки.")
    for uid in AUTHORIZED_USERS:
        try:
            await context.bot.send_message(uid, f"📢 Сообщение:\n\n{text}")
        except: continue
    await update.message.reply_text("✅ Рассылка завершена.")

async def exit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    AUTHORIZED_USERS.discard(uid)
    save_authorized()
    await update.message.reply_text("🚪 Вы вышли.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    await update.message.reply_text(f"👤 Авторизовано пользователей: {len(AUTHORIZED_USERS)}")

async def channelstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    chat = await bot.get_chat(CHANNEL_ID)
    members = await bot.get_chat_member_count(CHANNEL_ID)
    admins = await bot.get_chat_administrators(CHANNEL_ID)
    await update.message.reply_text(
        f"📊 Канал: {chat.title}\n👥 Подписчиков: {members}\n🛡️ Админов: {len(admins)}\n📃 Описание: {chat.description or '-'}"
    )

async def lastposts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    await update.message.reply_text("⚠️ Telegram Bot API не даёт доступ к истории канала. Возможность ограничена.")

async def moderation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    text = update.message.text.lower()
    if any(bad in text for bad in BANNED_WORDS):
        try:
            await update.message.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🔇 Сообщение удалено. Использование нецензурной лексики нарушает правила чата."
            )
        except Exception as e:
            logging.warning(f"Ошибка удаления: {e}")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("post", post_command))
application.add_handler(CommandHandler("broadcast", broadcast))
application.add_handler(CommandHandler("exit", exit_command))
application.add_handler(CommandHandler("stats", stats_command))
application.add_handler(CommandHandler("channelstats", channelstats_command))
application.add_handler(CommandHandler("lastposts", lastposts_command))
application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, moderation))

if __name__ == "__main__":
    print("✅ Админ-бот запущен.")
    application.run_polling()
