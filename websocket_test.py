import asyncio
import datetime
import random
import websockets
import json
@asyncio.coroutine
def msg_producer():
    _id = 0
    status = {0:'sleeping',1:'running', 2:'recruiting', 3:'pending'}
    while True:
        rndm = random.randint(0, 3)
        batt = random.randint(0,9)
        yield from asyncio.sleep(rndm)
        yield from q.put({'_id':_id, 'battery':batt, 'status':status[rndm]})
@asyncio.coroutine
def msg_producer2():
    _id = 1
    status = {0:'sleeping',1:'running', 2:'recruiting', 3:'pending'}
    while True:
        rndm = random.randint(0, 3)
        yield from asyncio.sleep(rndm)
        yield from q.put({'_id':_id, 'battery':rndm, 'status':status[rndm]})
@asyncio.coroutine
def time(websocket, path):
    while True:
        msg = yield from q.get()
        yield from websocket.send(json.dumps(msg))
q = asyncio.Queue()

start_server = websockets.serve(time, '127.0.0.1', 8080)
tasks = [start_server, msg_producer2(), msg_producer()]
asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
asyncio.get_event_loop().run_forever()