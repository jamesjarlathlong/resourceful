import asyncio
class A:
	def __init__(self):
		self.a = [1]
	@asyncio.coroutine
	def printer(self):
		while True:
			yield from asyncio.sleep(1)
			print('a: ', self.a)
a = A()
class B:
	def __init__(self):
		self.b = a.a
	@asyncio.coroutine
	def bprint(self)
loop = asyncio.get_event_loop()
tasks = [a.printer()]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
