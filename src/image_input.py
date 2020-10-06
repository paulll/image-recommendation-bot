import asyncio
#import sqlalchemy as sa
#from aiopg.sa import create_engine

from .image_search import find_image_by_file, KnownShitException, UnknownShitException
from .database import get_pool

from aiofiles.os import remove
from telethon import events, functions, Button
from telethon.tl.types import MessageMediaPhoto
from .client import client

groups = dict()
group_replies = dict()

@client.on(events.NewMessage)
async def handler(event):
	message = event.message
	if message.media and isinstance(message.media, MessageMediaPhoto):
		processing_msg = None
		if message.grouped_id:
			if not message.grouped_id in groups:
				groups[message.grouped_id] = 1
				group_replies[message.grouped_id] = await message.reply("Распознаю...")

				# state changed while replying
				if groups[message.grouped_id] != 1:
					await group_replies[message.grouped_id].edit("Распознаю... {} запланировано".format(groups[message.grouped_id]))
			else:
				groups[message.grouped_id] += 1
				if message.grouped_id in group_replies:
					await group_replies[message.grouped_id].edit("Распознаю... {} запланировано".format(groups[message.grouped_id]))
		else:
			processing_msg = await message.reply("Распознаю...")

		print('dl media..')
		file = await message.download_media()
		result = None

		print('find image..')

		try:
			result = await find_image_by_file(file)
		except KnownShitException:
			print('[!] Known Shit Happened')
			pass
		except Exception as e:
			print(e)
			await asyncio.sleep(60*5)
			try:
				result = await find_image_by_file(file)
			except Exception:
				print('[!] Unknown Shit Happened TWICE in a ROW! Aborting operation')

		print(result)

		# save like
		if result:
			pool = await get_pool()
			with (await pool.cursor()) as cur:
				await cur.execute('insert into local_likes (uid, imageid) values (%s, %s) on conflict do nothing', (
					event.message.from_id, 
					result
				))

		if message.grouped_id and groups[message.grouped_id]:
			groups[message.grouped_id] -= 1
			if groups[message.grouped_id] == 0:
				await group_replies[message.grouped_id].delete()
			else:
				await group_replies[message.grouped_id].edit("Распознаю... {} запланировано".format(groups[message.grouped_id]))
		if processing_msg:
			await processing_msg.delete()
		await remove(file)