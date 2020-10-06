import psycopg2.extras
from collections import Counter

from ..database import get_pool


async def predict(liked_images_ids, max_n=50, prod=True):
	pool = await get_pool()
	tag_weights = Counter()
	for imageid in liked_images_ids:
		async with pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
			await cursor.execute('select * from image_tags where imageid = %s', (imageid,))
			async for row in cursor:
				tag_weights.update({row['tagname']: 1})
	image_weights = Counter()
	for tagname, tag_weight in tag_weights:
		async with pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
			await cursor.execute('select * from image_tags where tagname = %s', (tagname,))
			async for row in cursor:
				image_weights.update(
					{row['imageid']: tag_weight / (cursor.arraysize + len(liked_images_ids) - tag_weight)})
	if prod:
		return list(x for x, _ in image_weights.most_common() if x not in liked_images_ids)[:max_n]
	return image_weights.most_common(max_n)
