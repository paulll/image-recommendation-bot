import random
import asyncio
import aiosqlite
import aiohttp
from time import time

from .models import simplest
from .client import client

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


async def post_worker():
	async with aiosqlite.connect('metadata.sqlite') as db:
		while True:
			time_start = time()
			time_to_next_check = time_start + check_interval + random.uniform(0, jitter)

			db.row_factory = aiosqlite.Row
			async with db.execute("select uid from local_users where datetime(last_post, 'unixepoch') < date(?, 'unixepoch')", (post_interval + int(time()),)) as cursor:
				async for user in cursor:
					print('[output] checking user: {}'.format(user['uid']))
					async with db.execute("select imageid from local_likes where uid=?", (user['uid'],)) as cursor2:
						user_likes = set(like['imageid'] for like in (await cursor2.fetchall()))
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
									await db.execute("replace into local_users (uid, last_post) values (?,?)", (user['uid'], int(time())))
									await db.execute("replace into local_likes (uid, imageid) values (?,?)", (user['uid'], int(rec)))
									await db.commit()

									# todo: feedback buttons (like / dislike)
									# todo: +moar similiar button
									# todo: +more pics button
									print('[output] uploading picture..')
									await client.send_file(user['uid'], file, progress_callback=action)
		time_end = time()
		if time_end < time_to_next_check:
			await asyncio.sleep(time_to_next_check - time_end)

client.loop.create_task(post_worker())