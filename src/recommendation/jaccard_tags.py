import asyncio
from collections import Counter, defaultdict

from sqlalchemy import select
from src.database import execute, image_tags, tag_image_amounts

async def image_weights_task(liked_images_ids, tagname, tag_likes_intersection, image_weights):
	async with execute(select([image_tags.c.imageid]).where(image_tags.c.tagname == tagname)) as cursor:
		rows = await cursor.fetchall()
		tag_weight = tag_likes_intersection/(len(rows) + len(liked_images_ids) - tag_likes_intersection)
		for row in rows:
			image_weights.update({ row.imageid: tag_weight })

tag_amounts_cache = None
async def predict(liked_images_ids, seen, max_n=50, prod=True):
	"""
	Predict liked images via collaborative filtering with jaccard index

	:param liked_images_ids: list of liked images ids
	:param max_n: max images to predict
	:param prod: if true, return only image ids that are not in liked_images_ids;
	else return [id, weight] pairs list for all predicted images
	:return: see :prod argument
	"""

	global tag_amounts_cache
	if not tag_amounts_cache:
		tag_amounts_cache = dict()
		async with execute(tag_image_amounts.select()) as cursor:
			async for row in cursor:
				tag_amounts_cache[row.tagname] = row.images
	
	tag_likes_intersections = Counter()
	for imageid in liked_images_ids:
		async with execute(select([image_tags.c.tagname]).where(image_tags.c.imageid==imageid)) as cursor:
			async for row in cursor:
				tag_likes_intersections.update({row.tagname: 1})
	print('[predict] tags: {}'.format(len(tag_likes_intersections)))
	
	image_weights = Counter()
	tasks = []

	tag_weights = Counter( dict((tag, intersections/(tag_amounts_cache[tag] + len(liked_images_ids) - intersections)) for tag,intersections in tag_likes_intersections.most_common() if tag in tag_amounts_cache))
	tags_to_fetch = list(x for x, _ in tag_weights.most_common(60))

	for tagname in tags_to_fetch:
		tag_likes_intersection = tag_likes_intersections[tagname]
		tasks.append(image_weights_task(liked_images_ids, tagname, tag_likes_intersection, image_weights))
	while True:
		done, pending = await asyncio.wait(tasks, timeout=2)
		tasks = pending
		if not len(tasks):
			break
		print('[predict] {} tags left'.format(len(tasks)))
	if prod:
		return list(x for x, _ in image_weights.most_common() if x not in seen)[:max_n]
	return image_weights.most_common(max_n)