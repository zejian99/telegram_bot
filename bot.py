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
        await update.message.reply_text("💬 Please start me using /start so we can organize your tasks together! 💖")
        return
    try:
        # Join all elements of context.args to form the task name, assuming the last element might be a date
        if len(context.args) > 1 and '-' in context.args[-1]:  # Check if the last argument might be a date
            due_date = datetime.datetime.strptime(context.args[-1], "%Y-%m-%d").date()
            task = ' '.join(context.args[:-1])  # Join all but the last as the task name
        else:
            due_date = None  # No date provided, task is recurring
            task = ' '.join(context.args)  # Join all elements to form the task name

        save_task(chat_id, task, due_date)

        if due_date:
            await update.message.reply_text(f"✅ Task '{task}' added with due date: {due_date}. Let's get this done! 💪")
        else:
            await update.message.reply_text(f"✅ Recurring task '{task}' added. I'll keep you posted! 📅")
    except IndexError:
        await update.message.reply_text("📝 Need to add a new task, my love? Here’s how you can tell me: \n"
    "*Usage:* `/add <task_name> [<due_date YYYY-MM-DD>]`\n"
    "*Example:* `/add Buy flowers 2022-12-25`\n"
    "Just type the task and when it’s due, and I’ll remember it for you! 🌷✨",
    parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("Oops! 🙈 Invalid date format. Please use YYYY-MM-DD format, like 2022-12-25.")


# Delete task command
async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not is_user_active(chat_id):
        await update.message.reply_text("💬 Please start me using /start so we can organize your tasks together! 💖")
        return
    try:
        # Join all elements of context.args to form the full task name
        task_name = ' '.join(context.args)
        result = supabase.table("Tasks").delete().eq("chat_id", chat_id).eq("task_name", task_name).execute()
        if result.data:
            await update.message.reply_text(f"🗑️ Task '{task_name}' deleted. More space for new adventures! 🌟")
        else:
            await update.message.reply_text("Hmm, I couldn't find that task. 🤔 Make sure it's spelled correctly!")
    except IndexError:
        await update.message.reply_text("🗑️ Want to clear a task? Just tell me like this:\n"
    "*Usage:* `/delete <task_name>`\n"
    "*Example:* `/delete Buy flowers`\n"
    "This will remove the task from your list, making room for new adventures! 🌺💖",
    parse_mode='Markdown')

# List all tasks command
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
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
        # Start of the reminder message
        reminder_message = "🌞 Good Morning, Beautiful! Here’s your love-filled reminder for the day: 🌞\n\n"
        
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