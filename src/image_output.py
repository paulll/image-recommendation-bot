import random
import asyncio
import aiohttp
import aiopg
from time import time

from telethon import events, functions
from telethon.tl.custom.button import Button

from .secrets import api_key
from .models import simplest
from .client import client
from .database import get_pool

import psycopg2.extras

post_interval = 60*60
check_interval = 60
jitter = 60

# debug
jitter, check_interval = 1, 5
post_interval = 60


session = aiohttp.ClientSession()

async def get_danbooru_photo(pic_id):
	global api_key
	#proxy = 'http://proxy-nossl.antizapret.prostovpn.org:29976'
	post_info_response = await session.get('https://danbooru.donmai.us/posts/{}.json?api_key={}'.format(pic_id, api_key))
	post_info = await post_info_response.json()
	if 'large_file_url' not in post_info:
		print('[error] post_info broken:', post_info)
		return None
	return post_info['large_file_url']

async def process_user(pool, user):
	print('[output] checking user: {}'.format(user['uid']))
	
	with (await pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor)) as image_cursor:
		await image_cursor.execute("select imageid,type from local_likes where uid=%s", (user['uid'],))
		all_likes = await image_cursor.fetchall();
		user_likes = set(like['imageid'] for like in all_likes if like['type'] == 'L')
		user_seen = set(like['imageid'] for like in all_likes)
		print('[output] obtained {} likes'.format(len(user_likes)))
		if len(user_likes) > 10:
			print('[output] predicting likes..')
			recs = await simplest.predict(user_likes, user_seen, 1)
			print('[output] predicted.')
			for rec in recs:
				async with client.action(user['uid'], 'photo') as action:
					print('[output] obtaining danbooru pic url..')
					file = await get_danbooru_photo(rec)
					print('[output] updating user data..')
					
					# mark in likes
					with (await pool.cursor()) as update_cursor:
						await update_cursor.execute("update local_users set last_post = %s where uid = %s", (int(time()), user['uid']))
						await update_cursor.execute("insert into local_likes (uid, imageid, type) values (%s,%s,'~') on conflict do nothing", (user['uid'], int(rec)))
					
					# todo: feedback buttons (like / dislike)
					# todo: +moar similiar button
					# todo: +more pics button
					print('[output] uploading picture..')
					buttons = [[
						Button.inline('👍', bytes(f'L{rec}', encoding='utf8')), # 🔥
						Button.inline('🤔', bytes(f'~{rec}', encoding='utf8')), # 
						Button.inline('👎', bytes(f'D{rec}', encoding='utf8'))  # 💩
					]]
					await client.send_file(user['uid'], file, progress_callback=action, buttons=buttons)

@client.on(events.CallbackQuery)
async def handler_(event):
	print(event)
	
	post = int(event.data[1:].decode('ascii'))
	feedback = event.data[:1].decode('ascii')
	source_message = await event.get_message()
	user = event.query.user_id

	if feedback == 'D':
		await source_message.delete()

	pool = await get_pool()
	if feedback != '~':
		with (await pool.cursor()) as update_cursor:
			await update_cursor.execute("update local_likes set type=%s where uid=%s and imageid=%s", (feedback, user, post))

	await source_message.edit(buttons=None)
	await event.answer()




async def post_worker():
	pool = await get_pool()
	while True:
		time_start = time()
		time_to_next_check = time_start + check_interval + random.uniform(0, jitter)
		
		with (await pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor)) as users_cursor:
			await users_cursor.execute("select uid from local_users where last_post < %s", (post_interval + int(time()),))
			async for user in users_cursor:
				await process_user(pool, user)

		time_end = time()
		if time_end < time_to_next_check:
			await asyncio.sleep(time_to_next_check - time_end)

client.loop.create_task(post_worker())