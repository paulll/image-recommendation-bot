import asyncio
from collections import Counter, defaultdict

from sqlalchemy import select
from src.database import execute, image_likes, user_like_amounts

async def image_weights_task(liked_images_ids, userid, user_likes_intersection, image_weights):
	async with execute(select([image_likes.c.imageid]).where(image_likes.c.userid == userid)) as cursor:
		rows = await cursor.fetchall()
		user_weight = user_likes_intersection/(len(rows) + len(liked_images_ids) - user_likes_intersection)
		for row in rows:
			image_weights.update({ row.imageid: user_weight })

user_amounts_cache = None
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
		async with execute(user_like_amounts.select()) as cursor:
			async for row in cursor:
				user_amounts_cache[row.userid] = row.likes
	
	user_likes_intersections = Counter()
	for imageid in liked_images_ids:
		async with execute(select([image_likes.c.userid]).where(image_likes.c.imageid==imageid)) as cursor:
			async for row in cursor:
				user_likes_intersections.update({row.userid: 1})
	print('[predict] users: {}'.format(len(user_likes_intersections)))
	
	image_weights = Counter()
	tasks = []

	user_weights = Counter( dict((user, intersections/(user_amounts_cache[user] + len(liked_images_ids) - intersections)) for user,intersections in user_likes_intersections.most_common() if user in user_amounts_cache))
	users_to_fetch = list(x for x, _ in user_weights.most_common(400))

	for userid in users_to_fetch:
		user_likes_intersection = user_likes_intersections[userid]
		tasks.append(image_weights_task(liked_images_ids, userid, user_likes_intersection, image_weights))
	while True:
		done, pending = await asyncio.wait(tasks, timeout=2)
		tasks = pending
		if not len(tasks):
			break
		print('[predict] {} users left'.format(len(tasks)))
	if prod:
		return list(x for x, _ in image_weights.most_common() if x not in seen)[:max_n]
	return image_weights.most_common(max_n)