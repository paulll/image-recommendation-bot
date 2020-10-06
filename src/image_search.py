import aiohttp
import asyncio
import re
import aiofiles

from aiofiles.os import remove
from os.path import normpath
from pyquery import PyQuery as pq
from .client import client

from throttler import throttle_simultaneous

IQDB_HOST = 'https://danbooru.iqdb.org/'
IQDB_MARKER_ERROR = '<!-- Failed...'
IQDB_MARKER_NO_RESULTS = 'No relevant matches'

session = aiohttp.ClientSession()

class UnknownShitException(Exception):
	pass
class KnownShitException(Exception):
	pass

@throttle_simultaneous(count=1)
async def find_image_by_file(file):
	result = None

	form = (
		('file', open(file, 'rb')),
		('MAX_FILE_SIZE', '8388608')
	)
	resp = await session.post(IQDB_HOST, data=form)
	body = await resp.text()

	if IQDB_MARKER_ERROR in body:
		raise KnownShitException()
	elif not 'Your image' in body:
		print(' --- unknown shit --- ')
		print(body)
		raise UnknownShitException()	
	elif IQDB_MARKER_NO_RESULTS not in body:
		doc = pq(body)
		for match in doc('#pages table')[:0:-1]:
			match_type = doc(match).find('tr').eq(0).text()
			match_source = doc(match).find('tr').eq(2).text()
			match_dims = doc(match).find('tr').eq(3).text()
			match_similarity = doc(match).find('tr').eq(4).text().split('%')[0]
			match_dims = doc(match).find('tr').eq(3).text()
			match_url = re.sub('^//', 'https://', doc(match).find('a').attr('href'))

			if match_type in {'Best match', 'Additional match'}:
				result = int(match_url.replace('https://danbooru.donmai.us/posts/', ''))
	return result
