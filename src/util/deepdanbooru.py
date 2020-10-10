import aiohttp

from pyquery import PyQuery as pq
from throttler import throttle_simultaneous

DEEPDANBOORU_HOST = 'http://kanotype.iptime.org:8003/deepdanbooru/upload'
session = aiohttp.ClientSession()

@throttle_simultaneous(count=1)
async def get_tags_by_file(file):
	result = []

	form = (
		('file', open(file, 'rb')),
	)
	resp = await session.post(DEEPDANBOORU_HOST, data=form)
	body = await resp.text()

	elif not 'tbody' in body:
		print(' --- unknown shit --- ')
		print(body)
		raise Exception('no tbody')
	else:
		doc = pq(body)
		for match in doc('tbody tr td a'):
			result.append(doc(match).text())
	return result
