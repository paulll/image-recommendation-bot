import psycopg2.extras
from collections import Counter, defaultdict
from sklearn.linear_model import LogisticRegression
from numpy import array, vstack, hstack

from src.database import get_pool

from .tanimoto_users import predict as predict_by_users
from .tanimoto_tags import  predict as predict_by_tags


async def get_images_scores(image_ids, pool):
	scores = []
	for imageid in image_ids:
		with (await pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor)) as cursor:
			await cursor.execute('select score from images where id = %s', (imageid,))
			async for row in cursor:
				scores.append(row['score'])
	return array(scores)

model = LogisticRegression(random_state=0)


async def learn(users_subset):
	pool = await get_pool()

	async def get_user_likes(userid):
		likes = set()
		with (await pool.cursor(cursor_factory=psycopg2.extras.RealDictCursor)) as cursor:
			await cursor.execute('select * from image_likes where userid = %s', (userid,))
			async for row in cursor:
				likes.add(row['imageid'])
		return likes

	async def get_user_part(user):
		user_likes = list(await get_user_likes(user))
		features_dict = defaultdict(lambda: [0., 0., 0., 0])
		for recommendation in await predict_by_users(user_likes, 1000, False):
			features_dict[recommendation[0]][0] = recommendation[1]
		for recommendation in await predict_by_tags(user_likes, 1000, False):
			features_dict[recommendation[0]][1] = recommendation[1]
		for actual_like in user_likes:
			features_dict[actual_like][3] = 1
		for imageid, score in zip(features_dict.keys(), await get_images_scores(features_dict.keys(), pool)):
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
	pool = await get_pool()
	features_dict = defaultdict(lambda: [0.,0.,0.])
	for recommendation in await predict_by_users(liked_images_ids, 1000, False):
		features_dict[recommendation[0]][0] = recommendation[1]
	for recommendation in await predict_by_tags(liked_images_ids, 1000, False):
		features_dict[recommendation[0]][1] = recommendation[1]
	for imageid, score in zip(features_dict.keys(), await get_images_scores(features_dict.keys(), pool)):
		features_dict[imageid][2] = score
	features = array(features_dict.values())
	predicted = model.predict(features)
	return list(image for image, liked in zip(predicted, features_dict.keys()) if liked)[:max_n]
