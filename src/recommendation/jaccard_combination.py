from collections import Counter, defaultdict
from sklearn.linear_model import LogisticRegression
from numpy import array, vstack, hstack
from sqlalchemy import select

from src.database import execute, images, image_likes

from .jaccard_users import predict as predict_by_users
from .jaccard_tags import  predict as predict_by_tags

async def get_images_scores(image_ids):
	scores = []
	for imageid in image_ids:
		async with execute(select(images.c.score).where(images.c.id==imageid)) as cursor:
			async for row in cursor:
				scores.append(row.score)
	return array(scores)

model = LogisticRegression(random_state=0)

async def learn(users_subset):
	async def get_user_likes(userid):
		likes = set()
		async with execute(image_likes.select().where(image_likes.c.userid == userid)) as cursor:
			async for row in cursor:
				likes.add(row.imageid)
		print('user {} has {} likes'.format(userid, len(likes)))
		return likes

	async def get_user_part(user):
		user_likes = list(await get_user_likes(user))
		if len(user_likes) < 10:
			return
		features_dict = defaultdict(lambda: [0., 0., 0., 0])
		for recommendation in await predict_by_users(user_likes, set(), 1000, False):
			features_dict[recommendation[0]][0] = recommendation[1]
		for recommendation in await predict_by_tags(user_likes, set(), 1000, False):
			features_dict[recommendation[0]][1] = recommendation[1]
		for actual_like in user_likes:
			features_dict[actual_like][3] = 1
		for imageid, score in zip(features_dict.keys(), await get_images_scores(features_dict.keys())):
			features_dict[imageid][2] = score
		return array(features_dict.values())

	features = array([[]])
	samples = array([])

	for user in users_subset:
		print('[learn] processing user', user)
		user_part = await get_user_part(user)
		if not user_part:
			continue
		features = hstack(features, user_part[:, 0:3])
		samples = vstack(samples, user_part[:, 3:4].T[0])

	model.fit(features, samples)
	print('[learn] learned params:', model.get_params())


async def predict(liked_images_ids, seen, max_n=50):
	features_dict = defaultdict(lambda: [0.,0.,0.])
	for recommendation in await predict_by_users(liked_images_ids, seen, 1000, False):
		features_dict[recommendation[0]][0] = recommendation[1]
	for recommendation in await predict_by_tags(liked_images_ids, seen, 1000, False):
		features_dict[recommendation[0]][1] = recommendation[1]
	for imageid, score in zip(features_dict.keys(), await get_images_scores(features_dict.keys())):
		features_dict[imageid][2] = score
	features = array(features_dict.values())
	predicted = model.predict(features)
	return list(image for image, liked in zip(predicted, features_dict.keys()) if liked)[:max_n]
