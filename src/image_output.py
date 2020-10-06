import random
import asyncio
import aiohttp
import aiopg
from time import time

from .models import simplest
from .client import client
import psycopg2.extras

post_interval = 60*60
check_interval = 60
jitter = 60

# debug
jitter, check_interval = 1, 5
post_interval = 60


session = aiohttp.ClientSession()

async def get_danbooru_photo(pic_id):
	proxy = 'http://proxy-nossl.antizapret.prostovpn.org:29976'
	post_info_response = await session.get('https://danbooru.donmai.us/posts/{}.json?'.format(pic_id), proxy=proxy)
	post_info = await post_info_response.json()
	return post_info['large_file_url']


async def process_user(pool, user):
	print('[output] checking user: {}'.format(user['uid']))
	
	with (await pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor)) as image_cursor:
		await image_cursor.execute("select imageid from local_likes where uid=%s", (user['uid'],))
		user_likes = set(like['imageid'] for like in (await image_cursor.fetchall()))
		print('[output] obtained {} likes'.format(len(user_likes)))
		if len(user_likes) > 10:
			print('[output] predicting likes..')
			recs = await simplest.predict(user_likes, 1)
			print('[output] predicted.')
			for rec in recs:
				async with client.action(user['uid'], 'photo') as action:
					print('[output] obtaining danbooru pic url..')
					file = await get_danbooru_photo(rec)
					print('[output] updating user data..')
					
					# mark in likes
					with (await pool.cursor()) as update_cursor:
						await update_cursor.execute("update local_users set last_post = %s where uid = %s", (int(time()), user['uid']))
						await update_cursor.execute("insert into local_likes (uid, imageid) values (%s,%s) on conflict do nothing", (user['uid'], int(rec)))
					
					# todo: feedback buttons (like / dislike)
					# todo: +moar similiar button
					# todo: +more pics button
					print('[output] uploading picture..')
					await client.send_file(user['uid'], file, progress_callback=action)


async def post_worker():
	pool = await get_pool()
	while True:
		time_start = time()
		time_to_next_check = time_start + check_interval + random.uniform(0, jitter)
		
		with (await pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor)) as users_cursor
			await users_cursor.execute("select uid from local_users where last_post < %s", (post_interval + int(time()),)):
			async for user in users_cursor:
				await process_user(pool, user)

		time_end = time()
		if time_end < time_to_next_check:
			await asyncio.sleep(time_to_next_check - time_end)

client.loop.create_task(post_worker())