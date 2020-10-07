import asyncio
import psycopg2.extras
from collections import Counter, defaultdict

from ..database import get_pool

user_amounts_cache = None
async def image_weights_task(liked_images_ids, userid, user_likes_intersection, image_weights, pool):
	global user_amounts_cache
	with (await pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor)) as cursor:
		await cursor.execute("select imageid from image_likes where userid = %s", (userid,))
		rows = await cursor.fetchall()
		user_weight = user_likes_intersection/(len(rows) + len(liked_images_ids) - user_likes_intersection)
		for row in rows:
			image_weights.update({ row['imageid']: user_weight })

async def predict(liked_images_ids, seen, max_n=50, prod=True):
	"""
	Predict liked images via collaborative filtering with jaccard index

	:param liked_images_ids: list of liked images ids
	:param max_n: max images to predict
	:param prod: if true, return only image ids that are not in liked_images_ids;
	else return [id, weight] pairs list for all predicted images
	:return: see :prod argument
	"""

	global user_amounts_cache
	if not user_amounts_cache:
		user_amounts_cache = dict()
		with (await pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor)) as cursor:
			await cursor.execute('select userid,likes from user_like_amounts')
			async for row in cursor:
				user_amounts_cache[row['userid']] = row['likes']


	pool = await get_pool()
	user_likes_intersections = Counter()
	for imageid in liked_images_ids:
		with (await pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor)) as cursor:
			await cursor.execute('select userid from image_likes where imageid = %s', (imageid,))
			async for row in cursor:
				user_likes_intersections.update({row['userid']: 1})
	print('[predict] users: {}'.format(len(user_likes_intersections)))
	
	image_weights = Counter()
	tasks = []

	user_weights = Counter( dict((user, intersections/(user_amounts_cache[user] + len(liked_images_ids) - intersections)) for user,intersections in user_likes_intersections.most_common() if user in user_amounts_cache))
	users_to_fetch = list(x for x, _ in user_weights.most_common(400))

	for userid in users_to_fetch:
		user_likes_intersection = user_likes_intersections[userid]
		tasks.append(image_weights_task(liked_images_ids, userid, user_likes_intersection, image_weights, pool))
	while True:
		done, pending = await asyncio.wait(tasks, timeout=2)
		tasks = pending
		if not len(tasks):
			break
		print('[predict] {} users left'.format(len(tasks)))
	if prod:
		return list(x for x, _ in image_weights.most_common() if x not in seen)[:max_n]
	return image_weights.most_common(max_n)