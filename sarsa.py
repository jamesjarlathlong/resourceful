import random


class Sarsa:
    def __init__(self, actions, epsilon=0.1, alpha=0.2, gamma=0.9):
        self.q = {}

        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma
        self.actions = actions

    def getQ(self, state, action):
        q = self.q.get((state, action.__name__), 0.0)
        return q

    def learnQ(self, state, action, reward, value):
        oldv = self.q.get((state, action.__name__), None)
        if oldv is None:
            self.q[(state, action.__name__)] = reward
        else:
            self.q[(state, action.__name__)] = oldv + self.alpha * (value - oldv)

    def chooseAction(self, state):
        available_actions = self.actions[state]
        if random.random() < self.epsilon:
            action = random.choice(available_actions)
        else:
            q = [self.getQ(state, a) for a in available_actions]
            maxQ = max(q)
            count = q.count(maxQ)
            #in the event of a tied max Q value
            if count > 1:
                best = [i for i in range(len(available_actions)) if q[i] == maxQ]
                i = random.choice(best)
            else:
                i = q.index(maxQ)

            action = available_actions[i]
        return action

    def learn(self, state1, action1, reward, state2, action2):
        print('learning: ', state1, action1, state2, reward)
        qnext = self.getQ(state2, action2)
        self.learnQ(state1, action1, reward, reward + self.gamma * qnext)