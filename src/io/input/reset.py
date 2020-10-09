import time
import aiosqlite

from telethon import events, functions
from src.client import client
from src.database import get_pool


@client.on(events.NewMessage)
async def handler(event):
	message = event.message
	if message.message.startswith('/reset'):
		pool = await get_pool()	
		msg = await message.respond("Секунду.. последнюю картинку обработаю")
		with (await pool.cursor()) as cursor:
			await cursor.execute("delete from local_likes where uid=%s", (message.from_id,))
		await msg.edit("Окей, я всё забыл. Давай по-новой")