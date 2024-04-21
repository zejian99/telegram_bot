import datetime
from telegram import Update
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, ContextTypes, ConversationHandler, MessageHandler, filters
from telegram import ReplyKeyboardMarkup
from supabase import create_client, Client

from admin import delete_task, is_user_active, load_tasks, save_task
from config import get_settings

# Supabase client initialization
url: str = get_settings().DATABASE_URL
key: str = get_settings().DATABASE_KEY  # Replace with your Supabase anon key
# supabase: Client = create_client(url, key)


LIST_TASKS, CHOOSE_TASK_TO_DELETE = range(3, 5)

async def start_delete(update: Update, context):
    chat_id = update.effective_chat.id
    if not is_user_active(chat_id):
        await update.message.reply_text("Please click /start to activate the bot before adding tasks. 🙏")
        return ConversationHandler.END
    # Fetch tasks from the database
    tasks = load_tasks(chat_id)
    if tasks:
        message = "🌼 Here's what you have on your plate:\n"
        message += "\n".join([f"{idx+1}. {task['task_name']}" for idx, task in enumerate(tasks)])
        message += "\n\nWhich task would you like to clear off? Just type the number: 💕"
        context.user_data['tasks'] = tasks  # Save tasks to context for later use
        await update.message.reply_text(message)
        return CHOOSE_TASK_TO_DELETE
    else:
        await update.message.reply_text("It looks like you don’t have any tasks to delete right now. 🌟")
        return ConversationHandler.END

async def choose_task_to_delete(update: Update, context):
    chat_id = update.effective_chat.id
    user_input = update.message.text.strip()
    try:
        task_idx = int(user_input) - 1
        if task_idx >= 0 and task_idx < len(context.user_data['tasks']):
            task_name = context.user_data['tasks'][task_idx]['task_name']
            # Delete the task from the database
            delete_task(chat_id, task_name)
            await update.message.reply_text(f"✅ Done! '{task_name}' has been removed from your list. 🗑️")
            return ConversationHandler.END
        else:
            await update.message.reply_text("Hmm, that number doesn’t seem right 🧐. Could you try again?")
            return CHOOSE_TASK_TO_DELETE
    except ValueError:
        await update.message.reply_text("Please type a valid number from the list above. 📝")
        return CHOOSE_TASK_TO_DELETE

async def cancel(update, context):
    await update.message.reply_text('No worries at all! Whenever you’re ready, just type /delete to try again. 💕', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

delete_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('delete', start_delete)],
    states={
        CHOOSE_TASK_TO_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_task_to_delete)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)