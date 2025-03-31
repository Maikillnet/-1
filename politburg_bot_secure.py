
import os
import logging
import asyncio
from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
from datetime import datetime
from telegram.constants import ChatType

# === ДАННЫЕ ПОЛЬЗОВАТЕЛЯ ===
TOKEN = "8053119583:AAEk2_DTDRqta2_gPuZ83DZkcebwyZ1nKPM"
CHANNEL_ID = "@politbyrg"
MONITORED_CHANNELS = [
    "@wisedruidd", "@barantchik", "@politjoystic", "@mariasergeyeva"
]

subscribers = set()
stats_file = "stats.txt"
BANNED_WORDS = [
    "хуй", "пизда", "ебать", "блядь", "мразь", "сука", "гандон", "даун", "чмо", "уебище",
    "идиот", "тварь", "сволочь", "жопа", "говно", "мудак", "сукa", "педик", "гей", "извращенец",
    "долбаёб", "дурак", "дурa", "шалава", "проститутка", "аутист", "обоссышься", "лох", "дебил",
    "кретин", "урод", "чурка", "негр", "нацист", "расист", "ссанина", "дрянь", "еблан", "петух"
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
application = ApplicationBuilder().token(TOKEN).build()

def save_stats():
    with open(stats_file, "w") as f:
        f.write("\n".join(str(uid) for uid in subscribers))

def load_stats():
    if os.path.exists(stats_file):
        with open(stats_file) as f:
            for line in f:
                subscribers.add(int(line.strip()))

load_stats()

# === КОМАНДЫ ===

# === ПАРОЛЬ ===
BOT_PASSWORD = "Mailmail20020921"
user_auth_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in subscribers:
        await update.message.reply_text("Вы уже авторизованы.")
        return

    user_auth_state[uid] = "awaiting_password"
    await update.message.reply_text("Введите пароль для активации:")

    uid = update.effective_user.id
    subscribers.add(uid)
    save_stats()
    await update.message.reply_text("Бот активирован. Готов передавать сигналы.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n"
        "/start — запустить бота\n"
        "/help — получить помощь\n"
        "/post <минуты> <текст> — запланировать пост\n"
        "/stats — посмотреть статистику\n"
        "/exit — завершить работу"
    )

async def exit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    subscribers.discard(uid)
    save_stats()
    await update.message.reply_text("Вы отключены от эфира.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Текущих подписчиков: {len(subscribers)}")

async def post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in subscribers:
        await update.message.reply_text("Вы не авторизованы. Используйте /start.")
        return

    msg = update.message
    caption = msg.caption if msg.caption else msg.text
    if not caption:
        return await msg.reply_text("⚠️ Укажи: <минуты> <текст>")

    try:
        minutes, text = int(caption.split()[0]), " ".join(caption.split()[1:])
    except:
        return await msg.reply_text("⚠️ Формат: <минуты> <текст>")

    await msg.reply_text(f"Сообщение будет отправлено через {minutes} минут.")
    await asyncio.sleep(minutes * 60)

    if msg.photo:
        await bot.send_photo(CHANNEL_ID, msg.photo[-1].file_id, caption=text)
    elif msg.video:
        await bot.send_video(CHANNEL_ID, msg.video.file_id, caption=text)
    else:
        await bot.send_message(CHANNEL_ID, text)

# === АНТИСПАМ ===
async def moderation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if any(bad in text for bad in BANNED_WORDS):
        try:
            await update.message.delete()
            await context.bot.send_message(chat_id=update.effective_chat.id,
                text="Сообщение удалено: нарушает правила.")
        except Exception as e:
            logging.warning(f"Ошибка удаления: {e}")


# === ОБРАБОТКА ПАРОЛЯ ===
async def password_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if user_auth_state.get(uid) == "awaiting_password":
        if update.message.text == BOT_PASSWORD:
            subscribers.add(uid)
            save_stats()
            user_auth_state.pop(uid)
            await update.message.reply_text("✅ Доступ подтверждён. Бот активирован.")
        else:
            await update.message.reply_text("❌ Неверный пароль.")

# === ХЕНДЛЕРЫ ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("exit", exit_command))
application.add_handler(CommandHandler("stats", stats_command))
application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, moderation))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), password_check))
application.add_handler(MessageHandler(filters.ALL, post_handler))

# === ЗАПУСК ===
if __name__ == "__main__":
    print("PolitBurgBot активирован.")
    application.run_polling()
