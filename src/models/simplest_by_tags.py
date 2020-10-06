import aiosqlite
from collections import Counter

async def predict(liked_images_ids, max_n=50):
	async with aiosqlite.connect('metadata.sqlite') as db:
		db.row_factory = aiosqlite.Row
		tag_weights = Counter()
		for imageid in liked_images_ids:
			async with db.execute('select * from image_tags where imageid=?', (imageid,)) as cursor:
				async for row in cursor:
					tag_weights.update({ row['tagname']: 1})
		image_weights = Counter()
		for tagname,tag_weight in tag_weights:
			async with db.execute('select * from image_tags where tagname=?', (tagname,)) as cursor:
				async for row in cursor:
					image_weights.update({ row['imageid']: tag_weight/(cursor.arraysize + len(liked_images_ids) - tag_weight) })
		return list( x for x,_ in image_weights.most_common() if x not in liked_images_ids)[:max_n]