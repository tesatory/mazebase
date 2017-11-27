import time 
import numpy as np


class MazeBaseWrapper(object):
    def __init__(self, factory, featurizer, args):
        self.factory = factory
        self.featurizer = featurizer
        self.env = self.factory.init_random_game()

    @property
    def observation_dim(self):
        obs = self.get_obs()
        return obs.size
            
    @property
    def num_actions(self):
        return len(self.factory.actions)

    @property
    def dim_actions(self):
        return 1
    
    def get_obs(self):
        #FIXME?  what about multi agent?
        obs = self.featurizer.to_tensor(self.env, self.env.agent)
        obs = obs.view(-1).numpy()
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
        return (obs, r, done, None)
    
    def display(self):
        self.env.display_ascii()
        time.sleep(0.5)
