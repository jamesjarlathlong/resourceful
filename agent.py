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
		"""discrete time"""
		yield from asyncio.sleep(0)
		print('getting modifiers', self)
		print('getting from q', self)
		modifiers = [self.sensing_q.get_nowait()[1] for i in range(len(self.sensing_q._queue))]
		print('modifiers: ', modifiers)
		combined = compose(modifiers)
		return combined
	@asyncio.coroutine
	def experience_environment(self):
		"""experiences results of actions from environment, and creates an observation"""
		while True:
			previous_state, previous_action = self.states[-1]
			state_modifier = yield from self.get_any_modifiers()
			print('got a state modifier ', state_modifier)
			tochange = previous_state
			new_state = state_modifier(tochange)
			reward = self.state_rewards(previous_state, new_state)
			self.writer(new_state)
			new_action = self.act(new_state)
			self.learn_from_experience(new_state, reward, new_action)
			self.action_q.put_nowait((new_state,new_action))
			self.states.append((new_state, new_action))
			#yield from asyncio.sleep(0.2)


	def learn_from_experience(self, new_state, reward, new_action):
		previous_state, previous_action = self.states[-1]
		self.learner.learn(previous_state, previous_action, reward, new_state, new_action)

	def act(self, new_state):
		action = self.learner.chooseAction(new_state)
		return action

def env_and_action_modifier(env_modifier, action, state):
	action_modified_state = action(state)
	env_modified_state = env_modifier(state, action_modified_state, action)
	return env_modified_state

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
			for i in self.env_actions:
				next_modifier = next(i)
				self.sensing_q.put_nowait((2,next_modifier))	
			print('sensing q: ',self.sensing_q.qsize(), self.sensing_q._queue)
	def modify_state(self, state, action):
		"""based on state and action find the valid environment 
		function, combine the action modification and env mod
		and return a function that performs both"""
		new_state = action(state)
		env_modifier = self.env_reactions[action.__name__]
		full_modifier = functools.partial(env_and_action_modifier, env_modifier, action)
		return full_modifier