import time
import numpy as np

def to_numpy_flat_recursive(x):
    if type(x) is list:
        for i,j in enumerate(x):
            x[i] = to_numpy_flat_recursive(j)
    else:
        return x.view(-1).numpy()

class MazeBaseWrapper(object):
    def __init__(self, factory, featurizer, args=None):
        self.factory = factory
        self.featurizer = featurizer
        self.env = self.factory.init_random_game()
        self.args = args

    @property
    def observation_dim(self):
        obs = self.get_obs()
        #fixme
        if hasattr(self.args, '__NUMPY__') and self.args.__NUMPY__:
            return obs.size
        else:
            return obs.size(0)

    @property
    def obs_size(self):
        obs = self.get_obs()
        return obs.size()

    @property
    def num_actions(self):
        return [len(self.factory.actions)]

    def get_obs(self):
        #FIXME?  what about multi agent?
        obs = self.featurizer.to_tensor(self.env, self.env.agent)
        if hasattr(self.args, '__NUMPY__') and self.args.__NUMPY__:
            if type(obs) == list:
                to_numpy_flat_recursive(obs)
            else:
                obs = obs.view(-1).numpy()
        else:
            #fixme
            obs = obs.view(-1)
        return obs

    def reset(self):
        self.env = self.factory.init_random_game()
        return self.get_obs()

    def step(self, action):
        #FIXME?  what about multi agent?
        action = self.factory.iactions[action[0]]
        self.env.act(action)
        self.env.update()
        obs = self.get_obs()
        done = not self.env.is_active()
        r = self.env.get_reward()
        return (obs, r, done)

    def display(self):
        self.env.display_ascii()
        time.sleep(0.5)
