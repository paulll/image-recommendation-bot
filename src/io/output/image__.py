import asyncio
import aiopg
import psycopg2.extras

from time import time
from telethon import events, functions
from telethon.tl.custom.button import Button
from collections import defaultdict

from src.recommendation import tanimoto_users
from src.client import client
from src.database import get_pool
from src.util.danbooru import get_picture 

users_locks = defaultdict(asyncio.Lock)
async def process_user(pool, user):
	await users_locks[user].acquire()

	print('[output] checking user: {}'.format(user['uid']))
	with (await pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor)) as image_cursor:
		await image_cursor.execute("select imageid,type from local_likes where uid=%s", (user['uid'],))
		all_likes = await image_cursor.fetchall();
		user_likes = set(like['imageid'] for like in all_likes if like['type'] == 'L')
		user_seen = set(like['imageid'] for like in all_likes)
		print('[output] obtained {} likes'.format(len(user_likes)))
		if len(user_likes) > 10:
			recs = await tanimoto_users.predict(user_likes, user_seen, 1)
			for rec in recs:
				async with client.action(user['uid'], 'photo') as action:
					print('[output] obtaining danbooru pic url..')
					file = await get_picture(rec)
					print('[output] updating user data..')
					
					# mark in likes
					with (await pool.cursor()) as update_cursor:
						await update_cursor.execute("update local_users set last_post = %s where uid = %s", (int(time()), user['uid']))
						await update_cursor.execute("insert into local_likes (uid, imageid, type) values (%s,%s,'~') on conflict do nothing", (user['uid'], int(rec)))
					
					print('[output] uploading picture..')
					buttons = [[
						Button.inline('👍', bytes(f'L{rec}', encoding='utf8')), # 🔥
						Button.inline('🤔', bytes(f'~{rec}', encoding='utf8')), # 
						Button.inline('👎', bytes(f'D{rec}', encoding='utf8'))  # 💩
					]]
					await client.send_file(user['uid'], file, progress_callback=action, buttons=buttons)
					users_locks[user].release()

@client.on(events.CallbackQuery)
async def handler_(event):
	print(event)
	
	post = int(event.data[1:].decode('ascii'))
	feedback = event.data[:1].decode('ascii')
	source_message = await event.get_message()
	user = event.query.user_id

	pool = await get_pool()
	if feedback != '~':
		with (await pool.cursor()) as update_cursor:
			await update_cursor.execute("update local_likes set type=%s where uid=%s and imageid=%s", (feedback, user, post))

	if feedback == 'D':
		await source_message.delete()
	else:
		await source_message.edit(buttons=None)
	await event.answer()
	await process_user(pool, {'uid': user})


async def post_worker():
	pool = await get_pool()
	with (await pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor)) as users_cursor:
		await users_cursor.execute("select uid from local_users where last_post < %s", (post_interval + int(time()),))
		async for user in users_cursor:
			await process_user(pool, user)


client.loop.create_task(post_worker())