import time
import aiosqlite

from telethon import events, functions
from .client import client


start_text = """
Привет!
Просто отправляй боту аниме-картинки, что тебе нравятся (вместо сохранёнок), - и он будет предлагать свои с учётом предпочтений. Получится как канал с картинками, только специально под твой изощренный вкус
"""


@client.on(events.NewMessage)
async def handler(event):
	message = event.message
	if message.message.startswith('/start'):
		async with aiosqlite.connect('metadata.sqlite') as db:
			await db.execute("replace into local_users (uid, last_post) values (?,?)", (message.from_id, 0))
			await db.commit()
		await message.respond(start_text)