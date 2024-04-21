import datetime
from telegram import Update
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, ContextTypes, ConversationHandler, MessageHandler, filters
from telegram import ReplyKeyboardMarkup
from supabase import create_client, Client

from admin import is_user_active, load_tasks, save_task, update_task_due_date
from config import get_settings

# Extending existing conversation states
LIST_TASKS_UPDATE, CHOOSE_TASK_TO_UPDATE, UPDATE_DUE_DATE = range(5, 8)

async def start_update(update: Update, context):
    chat_id = update.effective_chat.id
    if not is_user_active(chat_id):
        await update.message.reply_text("Please click /start to activate the bot before adding tasks. 🙏")
        return ConversationHandler.END
    # Fetch tasks from the database
    tasks = load_tasks(chat_id)
    if tasks:
        message = "📝 Here's a list of all your tasks, baby:\n"
        message += "\n".join([f"{idx+1}. {task['task_name']} - Due: {task['due_date']}" for idx, task in enumerate(tasks)])
        message += "\n\nWhich one would you like to update? Just type the number 💕:"
        context.user_data['tasks'] = tasks  # Save tasks to context for later use
        await update.message.reply_text(message)
        return CHOOSE_TASK_TO_UPDATE
    else:
        await update.message.reply_text("Looks like you don’t have any tasks to update right now. 🤷‍♀️")
        return ConversationHandler.END

async def choose_task_to_update(update: Update, context):
    user_input = update.message.text.strip()
    try:
        task_idx = int(user_input) - 1
        if task_idx >= 0 and task_idx < len(context.user_data['tasks']):
            context.user_data['selected_task'] = context.user_data['tasks'][task_idx]
            await update.message.reply_text(f"You picked: {context.user_data['selected_task']['task_name']} 💖\nNow, what's the new due date for this task? Please enter it in YYYY-MM-DD format:")
            return UPDATE_DUE_DATE
        else:
            await update.message.reply_text("Hmm, that number doesn’t seem right 🧐. Could you try again?")
            return CHOOSE_TASK_TO_UPDATE
    except ValueError:
        await update.message.reply_text("Please type a valid number from the list above. 📝")
        return CHOOSE_TASK_TO_UPDATE

async def update_due_date(update: Update, context):
    new_due_date = update.message.text.strip()
    try:
        datetime.datetime.strptime(new_due_date, '%Y-%m-%d')  # Validate date format
        task = context.user_data['selected_task']
        # Update the task in the database
        # supabase.table("Tasks").update({"due_date": new_due_date}).eq("chat_id", task['chat_id']).eq("task_name", task['task_name']).execute()
        update_task_due_date(task['chat_id'], task['task_name'], new_due_date)
        await update.message.reply_text(f"All set! The due date for '{task['task_name']}' is now {new_due_date}. We’re on track! 🌟")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Oops! That doesn’t look like a date. 🤔 Please enter the due date in YYYY-MM-DD format, like 2022-12-25.")
        return UPDATE_DUE_DATE

async def cancel(update, context):
    await update.message.reply_text('No problem at all! Whenever you’re ready, just type /update to pick up where we left off. 💕', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

update_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('update', start_update)],
    states={
        CHOOSE_TASK_TO_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_task_to_update)],
        UPDATE_DUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_due_date)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)