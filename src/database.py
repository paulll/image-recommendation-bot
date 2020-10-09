import aiopg
import sqlalchemy as sa

from contextlib import asynccontextmanager
from aiopg.sa import create_engine

metadata = sa.MetaData()

image_likes = sa.Table('image_likes', metadata,
	sa.Column('imageid', sa.Integer, sa.ForeignKey('images.id'), primary_key=True),
	sa.Column('userid', sa.Integer, primary_key=True)
)

image_tags = sa.Table('image_tags', metadata,
	sa.Column('imageid', sa.Integer, sa.ForeignKey('images.id'), primary_key=True),
	sa.Column('tagname', sa.String, primary_key=True)
)

images = sa.Table('images', metadata,
	sa.Column('id', sa.Integer, primary_key=True),
	sa.Column('score', sa.Integer),
	sa.Column('rating', sa.String(1)),
	sa.Column('md5', sa.String(32))
)

local_likes = sa.Table('local_likes', metadata,
	sa.Column('uid', sa.Integer, primary_key=True),
	sa.Column('imageid', sa.Integer, sa.ForeignKey('image.id'), primary_key=True),
	sa.Column('type', sa.String(1)),
)

local_users = sa.Table('local_users', metadata,
	sa.Column('uid', sa.Integer, primary_key=True),
	sa.Column('last_post', sa.Integer)
)

tag_image_amounts = sa.Table('tag_image_amounts', metadata,
	sa.Column('tagname', sa.String, primary_key=True),
	sa.Column('images', sa.Integer)
)

user_like_amounts = sa.Table('user_like_amounts', metadata,
	sa.Column('userid', sa.Integer, primary_key=True),
	sa.Column('likes', sa.Integer)
)


engine = None
async def connect():
	global engine
	engine = await create_engine(
		user='paulll',
		database='irb',
		host='127.0.0.1'
	)

class execute(object):
	def __init__(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs

	async def __aenter__(self):
		global engine
		if not engine:
			await connect()
		self.context = engine.acquire()
		return await (await self.context.__aenter__()).execute(*self.args, **self.kwargs)

	async def __aexit__(self, *args):
		await self.context.__aexit__(*args)

	async def __actually_await(self):
		global engine
		if not engine:
			await connect()
		async with engine.acquire() as conn:
			return await conn.execute(*self.args, **self.kwargs)

	def __await__(self):
		return self.__actually_await().__await__()
