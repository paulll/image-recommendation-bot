import time
import aiosqlite

from telethon import events, functions
from src.client import client
from src.database import execute, local_likes


@client.on(events.NewMessage)
async def handler(event):
	message = event.message
	if message.message.startswith('/reset'):
		msg = await message.respond("Секунду.. последнюю картинку обработаю")
		await execute(local_likes.delete().where(local_likes.uid == message.from_id))
		await msg.edit("Окей, я всё забыл. Давай по-новой")