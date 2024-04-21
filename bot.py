import logging
import datetime
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, ContextTypes, ConversationHandler, MessageHandler, filters
from telegram import ReplyKeyboardMarkup
from supabase import create_client, Client
from admin import add_user, fetch_active_users, fetch_all_tasks, is_user_active, load_tasks, save_task, set_user_active
from config import get_settings
from helper.add import add_conv_handler
from helper.delete import delete_conv_handler
from helper.update import update_conv_handler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# List all tasks command
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not is_user_active(chat_id):
        await update.message.reply_text("💬 Please start me using /start so we can organize your tasks together! 💖")
        return
    today = datetime.date.today().isoformat()  # Get today's date for comparison
    if not is_user_active(chat_id):
        await update.message.reply_text("💬 Please start me using /start so we can organize your tasks together! 💖")
        return
    tasks = load_tasks(chat_id)
    if not tasks:
        message = "No tasks at the moment. Time to relax and enjoy! 🍹😊"
    else:
        message = "Here are all your current tasks, sweetheart: 📝\n"
        for task in tasks:
            if task['due_date']:
                if task['due_date'] == today:
                    # Special styling for tasks due today
                    task_desc = f"🔥 *{task['task_name']}*: due *Today*! 🔥"
                else:
                    task_desc = f"📅 {task['task_name']}: due on {task['due_date']} 📅"
            else:
                # Styling for ongoing tasks
                task_desc = f"✨ {task['task_name']}: ongoing 💖✨"
            message += f"- {task_desc}\n"

    await update.message.reply_text(message, parse_mode='Markdown')

# Daily reminder job
async def daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today().isoformat()
    # Fetch all active users
    active_users = fetch_active_users()
    tasks = fetch_all_tasks()

    tasks_by_chat_id = {}
    for task in tasks:
        chat_id = task['chat_id']
        if chat_id in active_users:  # Only include tasks from active users
            if chat_id in tasks_by_chat_id:
                tasks_by_chat_id[chat_id].append(task)
            else:
                tasks_by_chat_id[chat_id] = [task]
    for chat_id, tasks in tasks_by_chat_id.items():
        # Start of the reminder message
        reminder_message = "🌞 Good Morning, Beautiful! Here’s your love-filled reminder for your recurring tasks: 🌞\n\n"
        
        # Checking and appending each task
        for task in tasks:
            if task['due_date'] is None or task['due_date'] <= today:
                if task['due_date'] is None:
                    task_desc = f"💖 {task['task_name']} - Recurring 💖"
                else:
                    task_desc = f"💖 {task['task_name']} - Due Today: {task['due_date']} 💖"
                reminder_message += f"- {task_desc}\n"

        # Add a closing line
        reminder_message += "\nLet’s make today amazing! I believe in you! 😘💪"
        try:
            await context.bot.send_message(chat_id=chat_id, text=reminder_message)
        except Exception as e:
            logging.error(f"Failed to send message to chat {chat_id}: {str(e)}")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)
    text = """
    🌟💖 Hello Beautiful! 💖🌟

I’m your personal reminder bot, here to help you manage your tasks with love and care! 💓 Here’s what I can do to make your life easier and keep our plans organized:

💝 /start - Wake me up and let the magic begin! This will start our session where you can command me as you please.

💝 /add - Got something new on your mind? Use this to create a new task. Just follow the format /add task_name [due_date YYYY-MM-DD] and I’ll take note!

💝 /delete - Need to make space for new adventures? Use this to delete any task you no longer need. Just type /delete task_name and consider it gone!

💝 /list - Want to see what’s on the agenda? Use this to list all your current tasks. I’ll display everything that’s planned.

💝 /stop - Need a break from me? Use this to stop all notifications and commands. Don’t worry, I’ll be here waiting whenever you want to start again.

Use these commands to interact with me anytime you like! I’m here to help you keep track of everything important to us. 💌👩‍❤️‍💋‍👨

Let’s keep our lives organized and full of love! 💕
    """
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Optionally, perform any cleanup here such as unsubscribing the user from a mailing list, etc.
    
    chat_id = update.effective_chat.id
    set_user_active(chat_id, False)  # Set the user as inactive

    await context.bot.send_message(chat_id=chat_id, text="💔 You've stopped the bot, my love. I'll miss reminding you about your tasks! If you change your mind, just type /start to bring me back. I’ll be here waiting and ready to help! 💖",
    parse_mode='Markdown')


if __name__ == '__main__':
    token = get_settings().BOT_TOKEN
    application = ApplicationBuilder().token(token).build()
    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(CommandHandler('list', list_tasks))
    application.add_handler(add_conv_handler)
    application.add_handler(delete_conv_handler)
    application.add_handler(update_conv_handler)

    # Schedule the daily reminder
    job_queue = application.job_queue
    reminder_time = datetime.time(hour=10)  # Set your preferred reminder time
    job_queue.run_daily(daily_reminder, time=reminder_time, days=(0, 1, 2, 3, 4, 5, 6))

    # Testing purpose, send the messge after 1 minute
    # job_queue.run_once(daily_reminder, when=30) 
    
    application.run_polling()