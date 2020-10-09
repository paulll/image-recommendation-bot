import aiohttp
from src.secrets import api_key

session = aiohttp.ClientSession()

async def get_picture(pic_id):
	global api_key
	proxy = 'http://proxy-nossl.antizapret.prostovpn.org:29976'
	post_info_response = await session.get('https://danbooru.donmai.us/posts/{}.json?api_key={}'.format(pic_id, api_key), proxy=proxy)
	post_info = await post_info_response.json()
	if 'large_file_url' not in post_info:
		print('[error] post_info broken:', post_info)
		return None
	return post_info['large_file_url']
