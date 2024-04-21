import logging
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, ContextTypes
from supabase import create_client, Client
from admin import add_user, is_user_active, set_user_active
from config import get_settings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Supabase client initialization
url: str = get_settings().DATABASE_URL
key: str = get_settings().DATABASE_KEY  # Replace with your Supabase anon key
supabase: Client = create_client(url, key)

# Load tasks from JSON file
def load_tasks(chat_id):
    result = supabase.table("Tasks").select("*").eq("chat_id", chat_id).execute()
    return result.data if result.data else []

def save_task(chat_id, task_name, due_date=None):
    task_data = {
        'chat_id': chat_id,
        'task_name': task_name,
        'due_date': str(due_date) if due_date else None
    }
    supabase.table("Tasks").insert(task_data).execute()


# Add task command
async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not is_user_active(chat_id):
        await update.message.reply_text("Please start the bot using /start.")
        return
    try:
        task = context.args[0]  # Task name
        if len(context.args) > 1:
            due_date = datetime.datetime.strptime(context.args[1], "%Y-%m-%d").date()
        else:
            due_date = None  # No date provided, task is recurring

        save_task(chat_id, task, due_date)

        if due_date:
            await update.message.reply_text(f"Task '{task}' added with due date: {due_date}.")
        else:
            await update.message.reply_text(f"Recurring task '{task}' added.")
    except IndexError:
        await update.message.reply_text("Usage: /add <task_name> [<due_date YYYY-MM-DD>]")
    except ValueError:
        await update.message.reply_text("Invalid date format. Please use YYYY-MM-DD format.")


# Delete task command
async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not is_user_active(chat_id):
        await update.message.reply_text("Please start the bot using /start.")
        return
    try:
        task_name = context.args[0]
        result = supabase.table("Tasks").delete().eq("chat_id", chat_id).eq("task_name", task_name).execute()
        if result.data:
            await update.message.reply_text(f"Task '{task_name}' deleted.")
        else:
            await update.message.reply_text("No such task found.")
    except IndexError:
        await update.message.reply_text("Usage: /delete <task_name>")

# List all tasks command
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not is_user_active(chat_id):
        await update.message.reply_text("Please start the bot using /start.")
        return
    tasks = load_tasks(chat_id)
    message = "All Tasks:\n"
    for task in tasks:
        task_desc = f"{task['task_name']}: due {task['due_date']}" if task['due_date'] else f"{task['task_name']}: non-expiring"
        message += f"- {task_desc}\n"
    if not tasks:
        message += "No tasks available."
    await update.message.reply_text(message)


# Daily reminder job
async def daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today().isoformat()
    response = supabase.table("Tasks").select("*").execute()
    tasks = response.data if response.data else []

    tasks_by_chat_id = {}
    for task in tasks:
        chat_id = task['chat_id']
        if chat_id in tasks_by_chat_id:
            tasks_by_chat_id[chat_id].append(task)
        else:
            tasks_by_chat_id[chat_id] = [task]

    for chat_id, tasks in tasks_by_chat_id.items():
        reminder_message = "Daily Tasks Reminder:\n"
        for task in tasks:
            if task['due_date'] is None or task['due_date'] <= today:
                task_desc = f"{task['task_name']} (Recurring)" if task['due_date'] is None else f"{task['task_name']} (Due: {task['due_date']})"
                reminder_message += f"- {task_desc}\n"
        try:
            await context.bot.send_message(chat_id=chat_id, text=reminder_message)
        except Exception as e:
            logging.error(f"Failed to send message to chat {chat_id}: {str(e)}")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)
    text = """
    Hi! I'm a reminder bot. I can help you remember your tasks.
    Commands:
    /add <task_name> <due_date YYYY-MM-DD>
    /delete <task_name> <due_date YYYY-MM-DD>
    /list

    Example:
    /add Homework 2020-12-31
    /delete Homework 2020-12-31

    The bot will send you a daily reminder of your tasks.
    """
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Optionally, perform any cleanup here such as unsubscribing the user from a mailing list, etc.
    
    chat_id = update.effective_chat.id
    set_user_active(chat_id, False)  # Set the user as inactive

    await context.bot.send_message(chat_id=chat_id, text="You have stopped the bot. You will no longer receive reminders.")


if __name__ == '__main__':
    token = get_settings().BOT_TOKEN
    application = ApplicationBuilder().token(token).build()

    # Handlers
    start_handler = CommandHandler('start', start)
    add_task_handler = CommandHandler('add', add_task)
    delete_task_handler = CommandHandler('delete', delete_task)
    list_tasks_handler = CommandHandler('list', list_tasks)

    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(CommandHandler('add', add_task))
    application.add_handler(CommandHandler('delete', delete_task))
    application.add_handler(CommandHandler('list', list_tasks))

    # Schedule the daily reminder
    job_queue = application.job_queue
    reminder_time = datetime.time(hour=8)  # Set your preferred reminder time
    # job_queue.run_daily(daily_reminder, time=reminder_time, days=(0, 1, 2, 3, 4, 5, 6))

    # Testing purpose, send the messge after 1 minute
    job_queue.run_once(daily_reminder, when=60) 
    
    application.run_polling()