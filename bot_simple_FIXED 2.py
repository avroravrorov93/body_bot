
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

CHOOSING_DAY, ENTER_SETS, ENTER_REPS = range(3)

WORKOUTS = {
    "A": ["Подтягивания", "Брусья", "Приседания", "Жим вверх", "Пресс"],
    "B": ["Отжимания", "Тяга к поясу", "Выпады", "Узкие отжимания", "Планка"],
    "C": ["Горизонтальная тяга", "Сгибания рук", "Жим от груди", "Трицепс", "Кор пресс"]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Фулбоди Бот 💪 Напиши /тренировка, чтобы начать!")

async def workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["A", "B", "C"]]
    await update.message.reply_text("Какой тип дня? (A, B или C)", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CHOOSING_DAY

async def choose_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = update.message.text
    context.user_data["day"] = day
    context.user_data["exercises"] = WORKOUTS[day]
    context.user_data["current"] = 0
    context.user_data["results"] = []
    await update.message.reply_text(f"{context.user_data['exercises'][0]} — сколько подходов?")
    return ENTER_SETS

async def enter_sets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["sets"] = update.message.text
    await update.message.reply_text("Сколько повторов?")
    return ENTER_REPS

async def enter_reps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ex = context.user_data["exercises"][context.user_data["current"]]
    sets = context.user_data["sets"]
    reps = update.message.text
    context.user_data["results"].append(f"{ex}: {sets}x{reps}")
    context.user_data["current"] += 1

    if context.user_data["current"] >= len(context.user_data["exercises"]):
        save_report(update.effective_user.id, context.user_data)
        msg = "✅ Отчёт сохранён:
" + "\n".join(context.user_data["results"])
        await update.message.reply_text(msg)
        return ConversationHandler.END

    next_ex = context.user_data["exercises"][context.user_data["current"]]
    await update.message.reply_text(f"{next_ex} — сколько подходов?")
    return ENTER_SETS

def save_report(user_id, data):
    filename = "data.json"
    report = {
        "user_id": user_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "day": data["day"],
        "results": data["results"]
    }
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    else:
        all_data = []

    all_data.append(report)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = "data.json"
    if not os.path.exists(filename):
        await update.message.reply_text("Нет сохранённых тренировок.")
        return
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_data = [d for d in data if d["user_id"] == update.effective_user.id]
    if not user_data:
        await update.message.reply_text("Ты ещё не тренировался 😅")
        return
    msg = "📊 Последние тренировки:

"
    for d in user_data[-3:]:
        msg += f"{d['date']} [{d['day']}]:\n" + "\n".join(d["results"]) + "\n\n"
    await update.message.reply_text(msg)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена тренировки. Возвращайся позже!")
    return ConversationHandler.END

def main():
    import os
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("тренировка", workout)],
        states={
            CHOOSING_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_day)],
            ENTER_SETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_sets)],
            ENTER_REPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_reps)],
        },
        fallbacks=[CommandHandler("отмена", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("прогресс", show_progress))
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
