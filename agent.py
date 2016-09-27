import asyncio
from qlearn import QLearn
from sarsa import Sarsa
import itertools
import functools
import json
import collections
import random
def compose(functions):
    """composes a list of functions from right to left"""
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)
class Agent:
	def __init__(self, actions_states, state_rewards, initial_state, initial_action, learning_method, qsize, eventloop):
		self.learner = learning_method(actions_states)
		self.states = collections.deque(maxlen=5)
		self.states.append((initial_state,initial_action)) #a LIFO queue of state, action tuples - most recent in last position
		self.state_rewards = state_rewards #a function with args (previous state, new state) returns values rewards
		self.action_q = asyncio.Queue()#agent generates actions to be consumed by environment
		self.sensing_q = asyncio.PriorityQueue(maxsize = qsize)#environment generates state modifiers and rewards to be consumed by agent
		self.action_q.put_nowait((initial_state,initial_action))
		self.loop = eventloop
	def writer(self, state):
		pass
	@asyncio.coroutine
	def get_any_modifiers(self):
		"""every second"""
		random_offset = 0.1+random.random()/10.
		print('getting modifiers', self)
		yield from asyncio.sleep(random_offset)
		print('getting from q', self)
		modifiers = [self.sensing_q.get_nowait()[1] for i in range(len(self.sensing_q._queue))]
		print('modifiers: ', modifiers)
		combined = compose(modifiers)
		return combined
	@asyncio.coroutine
	def experience_environment(self):
		"""experiences results of actions from environment, and creates an observation"""
		while True:
			state_modifier = yield from self.get_any_modifiers()
			print('got a state modifier ', state_modifier)
			previous_state, previous_action = self.states[-1]
			tochange = previous_state
			new_state = state_modifier(tochange)
			reward = self.state_rewards(previous_state, new_state)
			self.writer(new_state)
			new_action = self.act(new_state)
			self.learn_from_experience(new_state, reward, new_action)
			self.action_q.put_nowait((new_state,new_action))
			self.states.append((new_state, new_action))

	def learn_from_experience(self, new_state, reward, new_action):
		previous_state, previous_action = self.states[-1]
		self.learner.learn(previous_state, previous_action, reward, new_state, new_action)

	def act(self, new_state):
		action = self.learner.chooseAction(new_state)
		return action

class Environment:
	def __init__(self,reactions,actions, sensing_q, action_q):
		"""envreactions is a dictionary with valid modifying functions
		for each state,action pair"""
		self.env_reactions = reactions
		self.env_actions = actions
		self.sensing_q = sensing_q
		self.action_q = action_q
	@asyncio.coroutine
	def react_to_action(self):
		while True:
			state, action = yield from self.action_q.get()
			modifier = self.modify_state(state, action)
			print('sensing q before: ',self.sensing_q.qsize(), self.sensing_q._queue)
			self.sensing_q.put_nowait((0,modifier))
			print('sensing q: ',self.sensing_q.qsize(), self.sensing_q._queue)
	def modify_state(self, state, action):
		"""based on state and action find the valid environment 
		function, combine the action modification and env mod
		and return a function that performs both"""
		new_state = action(state)
		env_modifier = self.env_reactions[action.__name__]
		def env_and_action_modifier(env_modifier, action, state):
			action_modified_state = action(state)
			env_modified_state = env_modifier(state, action_modified_state, action)
			return env_modified_state
		full_modifier = functools.partial(env_and_action_modifier, env_modifier, action)
		return full_modifier


	
if __name__ == '__main__':
	import random
	import asyncio
	"""define our agent"""
	#======states=========#
	battery = range(10)
	hour = range(24)
	sleeping = [True, False]
	all_vars = [battery,hour,sleeping]
	states = itertools.product(*all_vars)
	#======actions========#
	def go_to_sleep(old):
		new = list(old)
		new[2] = True
		return tuple(new)
	def wakeup(old_w):
		new_w = list(old_w)
		new_w[2] = False
		return tuple(new_w)
	actions_states = {i:[go_to_sleep, wakeup] for i in states}
	#####rewards###########
	def state_rewards(state1, state2):
		if state2[0] == 0:
			return -10
		elif not state1[2] and not state2[2]:
			return 1
		else:
			return 0
	###initial state###
	initial_state = (5,0,True)
	agent = Agent(actions_states, state_rewards, initial_state, wakeup)
	"""now define our environment"""
	#=====autonomous actions=======#
	@asyncio.coroutine
	def time_action():
		print('starting')
		def increase_time(old_time):
			new_time = list(old_time)
			if new_time[1]!=23:
				new_time[1] += 1
			else:
				new_time[1]=0
			return tuple(new_time)
		while True:
			yield from asyncio.sleep(0.1)
			yield from sensing_q.put(increase_time)
	@asyncio.coroutine
	def battery_action():
		battery = 0
		hour = 1
		sleeping = 2
		sunny = True
		def adjust_battery(is_sunny, old_pow):
			new_pow = list(old_pow)
			if new_pow[hour] in range(0,12):
				if new_pow[sleeping]:
					new_pow[battery] += (1 + is_sunny*1)
					#increase by 1 if not sunny, by 2 if sunny
				else:
					new_pow[battery] -= (2 - is_sunny*1) 
					#decrease by 2 if not sunny, 1 if sunny
			if new_pow[hour] in range(12,24):
				if not new_pow[sleeping]:
					new_pow[battery] -=2
			if new_pow[battery]<0:
				new_pow[battery] = 0
			if new_pow[battery]>9:
				new_pow[battery] = 9
			return tuple(new_pow)
		while True:
			yield from asyncio.sleep(0.5) #to do add randomness
			if random.random()<0.1:
				sunny = not sunny
			adjust_battery_sunny = functools.partial(adjust_battery, sunny)
			yield from sensing_q.put(adjust_battery_sunny)
	#======reactions to agent actions==========#
	def reaction_func(state1,state2, action):
		return state2
	env_reactions = {'go_to_sleep':reaction_func, 'wakeup':reaction_func}
	env  = Environment(env_reactions,[time_action, battery_action])
	"""now run the simulation"""
	loop = asyncio.get_event_loop()
	tasks = [agent.experience_environment(), env.react_to_action()]
	for i in env.env_actions:
		tasks.append(i())
	def loop_stopper():
		loop.stop()
	loop.call_later(2000, loop_stopper) 
	print('running')
	loop.run_until_complete(asyncio.wait(tasks))
	loop.close()
