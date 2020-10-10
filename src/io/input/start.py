import time
import aiosqlite

from telethon import events, functions
from src.client import client
from src.database import execute, local_users

start_text = """
Привет!
Просто отправляй боту аниме-картинки, что тебе нравятся (вместо сохранёнок), - и он будет предлагать свои с учётом предпочтений. Получится как канал с картинками, только специально под твой изощренный вкус
"""


@client.on(events.NewMessage)
async def handler(event):
	message = event.message
	if message.message.startswith('/start'):
		await execute(local_users.insert({
			'uid': message.from_id,
			'last_post': 0
		}))
		await message.respond(start_text)