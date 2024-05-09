# Define states
import datetime
from telegram import Update
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters
from telegram import ReplyKeyboardMarkup

from admin import is_user_active, save_task, task_name_exists

TASK_NAME, TASK_TYPE, TASK_DATE = range(3)

async def start_add(update: Update, context):
    chat_id = update.effective_chat.id
    if not is_user_active(chat_id):
        await update.message.reply_text("Please click /start to activate the bot before adding tasks. 🙏")
        return ConversationHandler.END
    await update.message.reply_text("💖 Sweetheart, what's the task you'd like to add today?")
    return TASK_NAME

async def handle_task_name(update: Update, context):
    chat_id = update.effective_chat.id
    task_name = update.message.text.strip()
    if not task_name:
        await update.message.reply_text('Oops, looks like you forgot to type the task name. 😅 What would you like to call your task?')
        return TASK_NAME
    # Use the imported function to check if the task name already exists
    if task_name_exists(chat_id, task_name):
        await update.message.reply_text('Oh no, we already have a task with that name! 🙈 Try a different name, maybe?')
        return TASK_NAME
    context.user_data['task_name'] = task_name
    reply_keyboard = [['Recurring', 'Set a Due Date']]
    await update.message.reply_text('Got it! 😊 Now, tell me, is this a recurring task or does it need a specific due date?',
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return TASK_TYPE

async def handle_task_type(update: Update, context):
    task_type = update.message.text
    if task_type == 'Set a Due Date':
        await update.message.reply_text('What’s the due date for this task? 📅 Please enter it in YYYY-MM-DD format:')
        return TASK_DATE
    else:
        save_task(update.effective_chat.id, context.user_data['task_name'])
        await update.message.reply_text(f"✅ Recurring task '{context.user_data['task_name']}' added. I'll keep you posted! 📅")
        return ConversationHandler.END

async def handle_due_date(update: Update, context):
    try:
        due_date = datetime.datetime.strptime(update.message.text, '%Y-%m-%d').date()
        save_task(update.effective_chat.id, context.user_data['task_name'], due_date)
        await update.message.reply_text(f"✅ Task '{context.user_data['task_name']}' added with due date: {due_date}. Let's get this done! 💪")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text('Hmm...that doesn’t look like the right format for a date. 🤔 Can you try again using YYYY-MM-DD? Like 2022-12-25.')
        return TASK_DATE

async def cancel(update, context):
    await update.message.reply_text('No worries at all, we can always organize your tasks later! 💕 Just type /add whenever you’re ready.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# Setup the conversation handler
add_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('add', start_add)],
    states={
        TASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_name)],
        TASK_TYPE: [MessageHandler(filters.Regex('^(Recurring|Set a Due Date)$'), handle_task_type)],
        TASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_due_date)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)