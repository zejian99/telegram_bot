# Daily reminder job
import datetime

from flask import Flask, Response
import requests

from admin import fetch_active_users, fetch_all_tasks
from config import get_settings

app = Flask(__name__)

def daily_reminder():
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
        send_message(chat_id, reminder_message)

def send_message(chat_id, text):
    """Send a message to a chat using Telegram's sendMessage API."""
    url = f'https://api.telegram.org/bot{get_settings().BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, json=payload)
    return response.json()

@app.route("/", methods=['POST'])
def hello_world():
    return "Hello -> Serving on the reminder folder"

@app.route("/trigger-reminder", methods=['POST'])
def trigger_reminder_endpoint():
    # Call the modified daily reminder function
    try:
        daily_reminder()
        return Response('Reminder triggered', status=200)
    except Exception as e:
        return Response(f'Error triggering reminder: {str(e)}', status=500)
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8889)