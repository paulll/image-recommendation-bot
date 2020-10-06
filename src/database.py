import aiopg

pool = None


async def connect():
	global pool
	dsn = 'dbname=irb user=paulll host=127.0.0.1'
	pool = await aiopg.create_pool(dsn)


async def get_pool():
	global pool
	if not pool:
		await connect()
	return pool