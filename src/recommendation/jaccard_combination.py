from collections import Counter, defaultdict
from sklearn.linear_model import LogisticRegression
from numpy import array, vstack, hstack
from sqlalchemy import select
from statistics import mean

from src.database import execute, images, image_likes

from .jaccard_users import predict as predict_by_users
from .jaccard_tags import  predict as predict_by_tags

async def get_images_scores(image_ids):
	scores = []
	for imageid in image_ids:
		async with execute(select([images.c.score]).where(images.c.id==imageid)) as cursor:
			async for row in cursor:
				scores.append(row.score)
	return scores

model = LogisticRegression(random_state=0)
#model.coef_ = array([ 1.58825572e+00 -2.91863739e+01 -4.27467123e-04])
#model.classes_ = array([0, 1])

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
		if len(user_likes) < 20:
			return
		user_likes_subset = user_likes[:int(len(user_likes)*0.8)]
		check_subset = set(user_likes) - set(user_likes_subset)
		features_dict = defaultdict(lambda: [0., 0., 0., 0])
		for recommendation in await predict_by_users(user_likes_subset, user_likes_subset, 1000, False):
			features_dict[recommendation[0]][0] = recommendation[1]
		for recommendation in await predict_by_tags(user_likes_subset, user_likes_subset, 1000, False):
			features_dict[recommendation[0]][1] = recommendation[1]
		for actual_like in check_subset:
			features_dict[actual_like][3] = 1
		for imageid, score in zip(features_dict.keys(), await get_images_scores(features_dict.keys())):
			features_dict[imageid][2] = score
		return array(list(features_dict.values()))

	features = None
	samples = None

	for user in users_subset:
		print('[learn] processing user', user)
		user_part = await get_user_part(user)
		if user_part is None:
			continue
		features = vstack((features, user_part[:, 0:3])) if features is not None else array(user_part[:, 0:3]) 
		samples = hstack((samples, user_part[:, 3:4].T[0])) if samples is not None else array(user_part[:, 3:4].T[0])

	model.fit(features, samples)
	print('[learn] learned params:', model.coef_)


# [0.09324946323950108]*348968, [0.06630376996665409]*348968, [44.096567593590244]*348968
async def predict(liked_images_ids, seen, max_n=50):
	st_usr_w, st_tag_w, st_scores = [], [], []
	features_dict = defaultdict(lambda: [0.,0.,0.])
	for recommendation in await predict_by_users(liked_images_ids, seen, 50, False):
		features_dict[recommendation[0]][0] = recommendation[1]
		st_usr_w.append(recommendation[1])
	for recommendation in await predict_by_tags(liked_images_ids, seen, 50, False):
		features_dict[recommendation[0]][1] = recommendation[1]
		st_tag_w.append(recommendation[1])
	for imageid, score in zip(features_dict.keys(), await get_images_scores(features_dict.keys())):
		features_dict[imageid][2] = score
		st_scores.append(score)

	avg_usr_w = mean(st_usr_w)
	avg_tag_w = mean(st_tag_w)
	avg_score = mean(st_scores)

	proba_dict = {}
	for image, features in features_dict.items():
		proba_dict[image] = features[0]/avg_usr_w + features[1]/avg_tag_w*1.6 + features[0]/avg_score*0.4
	proba = Counter(proba_dict)

	parsed_images = len(st_scores)
	print(f'= [{avg_usr_w}]*{parsed_images}, [{avg_tag_w}]*{parsed_images}, [{avg_score}]*{parsed_images}')

	return list(x for x,_ in proba.most_common() if x not in seen)[:max_n]