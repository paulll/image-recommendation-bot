import time
import aiosqlite

from telethon import events, functions
from .client import client
from .database import get_pool


@client.on(events.NewMessage)
async def handler(event):
	message = event.message
	if message.message.startswith('/reset'):
		pool = await get_pool()	
		with (await pool.cursor()) as cursor:
			await cursor.execute("delete from local_likes where uid=%s", (message.from_id,))
		await message.respond("Окей, я всё забыл. Давай по-новой")