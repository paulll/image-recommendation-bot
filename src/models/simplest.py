import asyncio
import psycopg2.extras
from collections import Counter

from ..database import get_pool


async def image_weights_task(liked_images_ids, userid, user_weight, image_weights, pool):
	async with pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
		await cursor.execute("select * from image_likes where userid = %s", (userid,))
		rows = await cursor.fetchall()
		for row in rows:
			image_weights.update({ row['imageid']: user_weight/(len(rows) + len(liked_images_ids) - user_weight) })


async def predict(liked_images_ids, max_n=50, prod=True):
	"""
	Predict liked images via collaborative filtering with jaccard index

	:param liked_images_ids: list of liked images ids
	:param max_n: max images to predict
	:param prod: if true, return only image ids that are not in liked_images_ids;
	else return [id, weight] pairs list for all predicted images
	:return: see :prod argument
	"""

	pool = await get_pool()
	user_weights = Counter()
	for imageid in liked_images_ids:
		async with pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
			await cursor.execute('select * from image_likes where imageid = %s', (imageid,))
			async for row in cursor:
				user_weights.update({row['userid']: 1})
	image_weights = Counter()
	tasks = []
	for userid, user_weight in user_weights.items():
		tasks.append(image_weights_task(liked_images_ids, userid, user_weight, image_weights, pool))
	await asyncio.wait(tasks)
	if prod:
		return list(x for x, _ in image_weights.most_common() if x not in liked_images_ids)[:max_n]
	return image_weights.most_common(max_n)