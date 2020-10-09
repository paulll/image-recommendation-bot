import time
import aiosqlite

from telethon import events, functions
from src.client import client
from src.database import get_pool

start_text = """
Привет!
Просто отправляй боту аниме-картинки, что тебе нравятся (вместо сохранёнок), - и он будет предлагать свои с учётом предпочтений. Получится как канал с картинками, только специально под твой изощренный вкус
"""


@client.on(events.NewMessage)
async def handler(event):
	message = event.message
	if message.message.startswith('/start'):
		pool = await get_pool()	
		with (await pool.cursor()) as cursor:
			await cursor.execute("insert into local_users (uid, last_post) values (%s,%s) on conflict do nothing", (message.from_id, 0))
		await message.respond(start_text)