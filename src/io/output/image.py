import asyncio
import aiopg
import random

from time import time
from telethon import events, functions
from telethon.tl.custom.button import Button
from collections import defaultdict
from sqlalchemy import select, update

from src.database import execute, local_likes, local_users
from src.recommendation import jaccard_combination as predictor
from src.client import client
from src.util.danbooru import get_picture 

users_locks = defaultdict(asyncio.Lock)
async def process_user(user):
	await users_locks[user].acquire()

	print('[output] checking user: {}'.format(user))
	
	async with execute(local_likes.select().where(local_likes.c.uid==user)) as image_cursor:
		all_likes = await image_cursor.fetchall()
		user_likes = set(like.imageid for like in all_likes if like.type == 'L')
		user_seen = set(like.imageid for like in all_likes)
		
		print('[output] obtained {} likes'.format(len(user_likes)))
		if len(user_likes) > 10:
			recs = await predictor.predict(user_likes, user_seen, 1)
			for rec in recs:
				async with client.action(user, 'photo') as action:
					print('[output] obtaining danbooru pic url..')
					file = await get_picture(rec)
					print('[output] updating user data..')
					
					# mark in likes
					await execute(update(local_users).values({'last_post': int(time())}).where(local_users.c.uid == user))
					await execute(local_likes.insert().values(uid=user, imageid=rec, type='~'))
					
					print('[output] uploading picture..')
					buttons = [[
						Button.inline('👍', bytes(f'L{rec}', encoding='utf8')), # 🔥
						Button.inline('🤔', bytes(f'~{rec}', encoding='utf8')), # 
						Button.inline('👎', bytes(f'D{rec}', encoding='utf8'))  # 💩
					]]
					for i in range(5):
						try:
							await client.send_file(user, file, progress_callback=action, buttons=buttons)
							users_locks[user].release()
							return
						except Exception as e:
							print(e)
							print('retrying...')
							continue
					print('..failed, trying next picture')
					users_locks[user].release()
					await process_user(user)
					

@client.on(events.CallbackQuery)
async def handler_(event):
	print(event)
	
	post = int(event.data[1:].decode('ascii'))
	feedback = event.data[:1].decode('ascii')
	source_message = await event.get_message()
	user = event.query.user_id

	if feedback != '~':
		await execute(update(local_likes).values({'type': feedback}).where((local_likes.c.uid==user) & (local_likes.c.imageid==post)))

	if feedback == 'D':
		await source_message.delete()
	else:
		await source_message.edit(buttons=None)
	await event.answer()
	await process_user(user)

async def post_worker():
	#learn_users = random.choices(range(0,100_000), k=100)
	#await predictor.learn(learn_users)
	processed_users = set()
	while True:
		async with execute(select([local_users.c.uid])) as users_cursor:
			async for user in users_cursor:
				if user in processed_users:
					continue
				await process_user(user.uid)
				processed_users.add(user)
			await asyncio.sleep(10)



client.loop.create_task(post_worker())