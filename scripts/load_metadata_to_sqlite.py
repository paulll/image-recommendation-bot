import glob
import asyncio
import aiosqlite
import json_lines
import asyncpool
import logging

from os.path import isfile

# image_tags = {imageid, tagname}
# image_likes = {imageid, userid}
# images = {id, score, rating, md5}

progress = 0;

async def process_line(db, img):
	global progress

	tasks = []
	await db.execute('replace into images (id, score, rating, md5) values (?, ?, ?, ?)', [
		int(img['id']), 
		int(img['score']),
		img['rating'],
		img['md5']
	])

	for tag in img['tags']:
		tasks.append(db.execute('insert into image_tags (imageid, tagname) values (?, ?) on conflict do nothing', [
			int(img['id']), 
			tag['name']
		]))

	for u in img['favs']:
		tasks.append(db.execute('insert into image_likes (imageid, userid) values (?, ?) on conflict do nothing', [
			int(img['id']), 
			int(u)
		]))

	await asyncio.wait(tasks)
	progress += 1
	if progress % 10000 == 0:
		print('[*] progress: {} entries loaded (~{:.2f}%)'.format(progress, 100*progress/3_741_623))
	


async def process_file(filename):
	loop = asyncio.get_running_loop()
	async with aiosqlite.connect('metadata.sqlite') as db:
		with open(filename, 'rb') as file:
			async with asyncpool.AsyncPool(loop, num_workers=500, name="LineProcessors", worker_co=process_line, max_task_time=60*5, logger=logging.getLogger("LineProcessorPool")) as pool:
				for img in json_lines.reader(file):
					await pool.push(db, img)
			print('[*] progress: finalizing file {} to database..'.format(filename))
			await db.commit()
			print('[*] progress: done finalizing')

async def main():
	loop = asyncio.get_running_loop()
	for filename in glob.iglob('metadata/2019*', recursive=False):
		if isfile(filename):
			await process_file(filename)

asyncio.get_event_loop().run_until_complete(main())