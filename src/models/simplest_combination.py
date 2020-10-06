import aiosqlite
from collections import Counter, defaultdict
from sklearn.linear_model import LogisticRegression
from numpy import array, vstack, hstack

async def predict_by_users(liked_images_ids, max_n=50):
	async with aiosqlite.connect('metadata.sqlite') as db:
		db.row_factory = aiosqlite.Row
		user_weights = Counter()
		for imageid in liked_images_ids:
			async with db.execute('select * from image_likes where imageid=?', (imageid,)) as cursor:
				async for row in cursor:
					user_weights.update({ row['userid']: 1})
		image_weights = Counter()
		for userid, user_weight in user_weights:
			async with db.execute('select * from image_likes where userid=?', (userid,)) as cursor:
				async for row in cursor:
					image_weights.update({ row['imageid']: user_weight/cursor.arraysize })
		return image_weights.most_common(max_n)

async def predict_by_tags(liked_images_ids, max_n=50):
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
					image_weights.update({ row['imageid']: tag_weight/cursor.arraysize })
		return image_weights.most_common(max_n)

async def get_images_scores(image_ids):
	async with aiosqlite.connect('metadata.sqlite') as db:
		scores = []
		for imageid in image_ids:
			async with db.execute('select score from images where id=?', (imageid,)) as cursor:
				async for row in cursor:
					scores.append(row['score'])
		return array(scores)

model = LogisticRegression(random_state=0)

async def learn(users_subset):
	async with aiosqlite.connect('metadata.sqlite') as db:
		db.row_factory = aiosqlite.Row
		async def get_user_likes(userid):
			likes = set()
			async with db.execute('select * from image_likes where userid=?', (userid,)) as cursor:
				async for row in cursor:
					likes.add(row['imageid'])
			return likes

		async def get_user_part(user):
			user_likes = list(await get_user_likes(user))
			features_dict = defaultdict(lambda: [0.,0.,0.,0])
			for recommendation in await predict_by_users(user_likes, 1000)
				features_dict[recommendation[0]][0] = recommendation[1]
			for recommendation in await predict_by_tags(user_likes, 1000)
				features_dict[recommendation[0]][1] = recommendation[1] 
			for actual_like in user_subset_likes:
				features_dict[actual_like][3] = 1
			for imageid, score in zip(features_dict.keys(), get_images_scores(features_dict.keys())):
				features_dict[imageid][2] = score
			return array(features_dict.values())

		features = array([[]])
		samples = array([])

		for user in users_subset:
			user_part = await get_user_part(user)
			features = hstack(features, user_part[:, 0:3])
			samples = vstack(samples, user_part[:, 3:4].T[0])

		model.fit(features, samples)

async def predict(liked_images_ids, max_n=50):
	features_dict = defaultdict(lambda: [0.,0.,0.])
	for recommendation in await predict_by_users(liked_images_ids, 1000)
		features_dict[recommendation[0]][0] = recommendation[1]
	for recommendation in await predict_by_tags(liked_images_ids, 1000)
		features_dict[recommendation[0]][1] = recommendation[1]
	for imageid, score in zip(features_dict.keys(), get_images_scores(features_dict.keys())):
		features_dict[imageid][2] = score
	features = array(features_dict.values())
	predicted = model.predict(features)
	return list(image if liked for image, liked in zip(predicted, features_dict.keys()) )[:max_n]