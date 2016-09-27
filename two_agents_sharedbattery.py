import os
from agent import *
import asyncio
from qlearn import QLearn
from sarsa import Sarsa
import itertools
import functools
import json
import random
import sklearn
import collections
import websockets
import json
import copy
import time
import random
###Helper functions###
def merge(dicts):
    super_dict = collections.defaultdict(list)
    for d in dicts:
        for k, v in d.items():
            super_dict[k]+=v
    return super_dict
def tuple_namer(name,tupl):
    """convert an unnamed state tuple
    to a namedtuple object"""
    tupl_templ = collections.namedtuple(name, 'battery status neighbour nstat')
    named = tupl_templ(battery = tupl[0], status = tupl[1], neighbour = tupl[2], nstat = tupl[3])
    return named
def dictionary_saver(d, filename):
    """d is a dictionary whose keys are of the form (namedtuple, 'string')"""
    json_friendly_d = {json.dumps(k):v for k,v in d.items()}
    sklearn.externals.joblib.dump(json_friendly_d, filename)
def tracker_saver(d, filename):
    """d is a dictionary whose keys are of the form (namedtuple, 'string')"""
    json_friendly_d = {json.dumps(k):json.dumps(v) for k,v in d.items()}
    sklearn.externals.joblib.dump(json_friendly_d, filename)
#======actions========#
def go_to_sleep(old):
    new = old._replace(status = 'sleeping')
    return new
def wakeup(old):
    new = old._replace(status = 'running')
    return new
def noop(old):
    print('noop')
    return copy.deepcopy(old)
def create_action_states(states):
    actions_states_sleeping = {i:[noop, wakeup] for i in states if i.status=='sleeping'}
    actions_states_running = {i:[go_to_sleep, noop] for i in states if i.status == 'running'}
    return merge([actions_states_sleeping, actions_states_running]) 
#####rewards###########
def state_rewards(state1, state2):
    initial_reward = 0
    if (state2.status == 'sleeping' and state2.nstat=='sleeping'):
        initial_reward -=50
    if state2.status =='running' or state2.nstat=='running':
        initial_reward += 20
    if state1.status !=state2.status:
        initial_reward -= 5
    if state2.battery == 0:
        initial_reward = -50
    return initial_reward
###message passing
def find_lead(qs,recruiter):
    """for recruiter, find potential helper"""
    all_candidates = [k for k in qs if k!=recruiter]
    return all_candidates[0]
def broadcast_change(old_state, new_state):
    """gets called when a sensor changes
    from sleeping to awake, notifies the other
    sensors of this change"""
    def neighbor_changed(old_other, new_other,old_self):
        new_self = old_self._replace(neighbour=new_other.battery, nstat= new_other.status)
        return new_self
    update_from = type(new_state).__name__
    update_to = find_lead(qs, update_from)
    print('updating from: ', update_from, ' to: ', update_to)
    neighbor_change_func = functools.partial(neighbor_changed,old_state, new_state)
    qs[update_to].update((1,neighbor_change_func))     
"""environments"""
#=====autonomous actions=======#
@asyncio.coroutine
def battery_action(q):
    sunny = True
    def adjust_battery(is_sunny, sensor):
        if sensor.status =='sleeping':
            new_battery = sensor.battery + (1 + is_sunny*1)#increase by 1 if not sunny, by 2 if sunny
            sensor = sensor._replace(battery=new_battery)
        else:
            new_battery = sensor.battery - (2 - is_sunny*1)
            sensor = sensor._replace(battery=new_battery)
        if sensor.battery<=0:
            sensor = sensor._replace(battery=0)
        if sensor.battery>=10:
            sensor = sensor._replace(battery=10)
        return sensor
    while True:
        #if random.random()<0.1:
        #    sunny = not sunny
        adjust_battery_sunny = functools.partial(adjust_battery, sunny)
        yield from asyncio.sleep(0.2)
        print('putting battery action on the q: ',q.qsize(),  q._queue)
        priority = random.uniform(2.01, 2.99) #we don't care about the order of adjust battery actions
        #just want to make sure they don't collide
        q.put_nowait((priority,adjust_battery_sunny))
#======reactions to agent actions==========#
def reaction_default(state1,state2, action):
    if state1.battery!=state2.battery or state1.status!=state2.status:
        print('broadcasting change')
        broadcast_change(state1, state2)
    return state2
"""speak to outside world"""
def writer(self, state):
    t = self.loop.time()-self.loop.t0
    name_id_map = {'Sensor1':0, 'Sensor2':1}
    idee = name_id_map[type(state).__name__]
    update = (t,{'_id':idee, 'battery':state.battery, 'status':state.status, 'neighbour': state.neighbour})
    print('update: ', update)
    writerq.append(update)
@asyncio.coroutine
def socketwriter(websocket, path):
    while True:
        msg = yield from writerq.get()
        print('msg: ', msg)
        yield from websocket.send(json.dumps(msg[1]))
"""special update function to ensure only latest event
   with info about neighbour is kept on the queue"""
def update(self, new_item):
    priority_level = new_item[0]
    def matching_level(element, priority_level):
        return element[0]==priority_level
    try:
        match_generator = (index for index,element in enumerate(self._queue)
                           if matching_level(element, priority_level))
        matching_index = next(match_generator)
        self._queue[matching_index] = new_item
    except StopIteration:
        self.put_nowait(new_item)
asyncio.PriorityQueue.update = update
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    t0 = loop.time()
    loop.t0 = t0
    """States"""
    battery = range(11)
    status = ['sleeping', 'running']
    neighbour = range(11)
    nstat = ['sleeping', 'running']
    all_vars = [battery,status, neighbour, nstat]
    state_combinations = list(itertools.product(*all_vars))
    """websocket comm"""
    Agent.writer = writer
    """agent 1"""
    states1 = [tuple_namer('Sensor1', i) for i in state_combinations]
    initial_state1 = tuple_namer('Sensor1', (3,'running', 6, 'running'))
    actions_states1 = create_action_states(states1)
    agent1 = Agent(actions_states1, state_rewards, initial_state1, wakeup, Sarsa, 1011, loop)
    """agent 2"""
    states2 = [tuple_namer('Sensor2', i) for i in state_combinations]
    initial_state2 = tuple_namer('Sensor2', (6,'running', 3, 'running'))
    actions_states2 = create_action_states(states2)
    agent2 = Agent(actions_states2, state_rewards, initial_state2, wakeup, Sarsa, 1022, loop)
    """message passing between agents"""
    qs = {'Sensor1':agent1.sensing_q, 'Sensor2':agent2.sensing_q}
    """message passing to websocket"""
    writerq = []#asyncio.PriorityQueue(maxsize = 2048)
    start_server = websockets.serve(socketwriter, '127.0.0.1', 8090)
    """now define our environments"""
    env_reactions = {'go_to_sleep':reaction_default, 'wakeup':reaction_default,
                 'noop':reaction_default}
    env1 = Environment(env_reactions,[copy.deepcopy(battery_action)], agent1.sensing_q, agent1.action_q)
    env2 = Environment(env_reactions,[copy.deepcopy(battery_action)], agent2.sensing_q, agent2.action_q)
    """now run the simulation"""
    tasks = [agent1.experience_environment(), env1.react_to_action(),
             agent2.experience_environment(), env2.react_to_action(),start_server]
    for i in env1.env_actions:
        tasks.append(i(agent1.sensing_q))
    for j in env2.env_actions:
        tasks.append(j(agent2.sensing_q))
    def loop_stopper():
        print('loop stopper')
        loop.stop()
        print('saving')
        sklearn.externals.joblib.dump(writerq, 'batt_writer')
        dictionary_saver(agent1.learner.q, 'agent1_batt')
        tracker_saver(agent1.learner.updatecount, 'agent1_batthist')
        dictionary_saver(agent2.learner.q, 'agent2_batt')
        tracker_saver(agent2.learner.updatecount, 'agent2_batthist')
        print('saved')     
    loop.call_later(1800, loop_stopper) 
    loop.run_until_complete(asyncio.wait(tasks))