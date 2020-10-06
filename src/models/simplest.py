import aiosqlite
import asyncio
from collections import Counter

async def image_weights_task(liked_images_ids, userid, user_weight, image_weights, db):
	async with db.execute('select * from image_likes where userid=?', (userid,)) as cursor:
		rows = await cursor.fetchall()
		for row in rows:
			image_weights.update({ row['imageid']: user_weight/(len(rows) + len(liked_images_ids) - user_weight) })

async def predict(liked_images_ids, max_n=50):
	async with aiosqlite.connect('metadata.sqlite') as db:
		db.row_factory = aiosqlite.Row
		user_weights = Counter()
		for imageid in liked_images_ids:
			async with db.execute('select * from image_likes where imageid=?', (imageid,)) as cursor:
				async for row in cursor:
					user_weights.update({ row['userid']: 1})
		image_weights = Counter()
		tasks = []
		for userid, user_weight in user_weights.items():
			tasks.append(image_weights_task(liked_images_ids, userid, user_weight, image_weights, db))
		await asyncio.wait(tasks)
		return list( x for x,_ in image_weights.most_common() if x not in liked_images_ids)[:max_n]