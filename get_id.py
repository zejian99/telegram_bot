import asyncio
import telegram
from config import get_settings

"""
Make sure you have filled in the credentials.py file with your own bot token
By running this script, you can get the chat id
"""

async def main():
    bot = telegram.Bot(get_settings().BOT_TOKEN)
    async with bot:
        # print(await bot.get_me())  ## get the bot information
        print((await bot.get_updates())[2])  ## See the bot received messages and get the chat id

if __name__ == '__main__':
    asyncio.run(main())