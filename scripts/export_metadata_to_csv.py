import glob
import json_lines
import os

from os.path import isfile

# image_tags = {imageid, tagname}
# image_likes = {imageid, userid}
# images = {id, score, rating, md5}
						
def main():
	progress = 0
	with open('tags.csv', 'w') as tags:
		with open('likes.csv', 'w') as likes:
			with open('images.csv', 'w') as images:
				for filename in glob.iglob('metadata/2019*', recursive=False):
					if isfile(filename):
						with open(filename, 'rb') as file:
							for img in json_lines.reader(file):

								images.write('{},{},{},{}\n'.format(
									int(img['id']), 
									int(img['score']),
									img['rating'],
									img['md5']
								))

								for tag in img['tags']:
									tags.write('{},{}\n'.format(
										int(img['id']), 
										tag['name']
									))

								for u in img['favs']:
									likes.write('{},{}\n'.format(
										int(img['id']), 
										int(u)
									))

								progress += 1
								if progress % 10000 == 0:
									print('[*] progress: {} entries loaded (~{:.2f}%)'.format(progress, 100*progress/3_741_623))

main()