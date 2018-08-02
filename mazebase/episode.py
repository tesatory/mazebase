import numpy as np

import mazebase.action_utils as action_utils


class EpisodeRunner(object):
    def __init__(self, env_maker, policy_net, value_net, args):
        self.env = env_maker(args.config_path)
        self.display = False
        self.policy_net = policy_net
        #fixme
        self.value_net = value_net
        self.args = args

        self.total_reward = 0
        self.total_steps = 0
        self.success = 0

    def quit(self):
        pass

    def reset(self):
        pass

    def get_episode(self):
        env = self.env
        policy_net = self.policy_net
        args = self.args
        episode = []
        state = self.env.reset()
        if self.display:
            env.display()
        success = 0
        for t in range(args.max_steps):
            #TODO get rid of action_utils
            action = action_utils.select_action(args, policy_net, state)
            action, actual = action_utils.translate_action(args, env, action)
            next_state, reward, done = env.step(actual)
            if self.display:
                env.display()
            mask = 1

            if done:
                success = 1

            done = done or t == args.max_steps - 1
            if done:
                mask = 0
            if args.__NUMPY__:
                episode.append([state, np.array([action]), mask, next_state, reward])
            else:
                episode.append([state, action, mask, next_state, reward])
            state = next_state
            if done:
                break
        total_steps = len(episode)
        total_reward = sum(x[4] for x in episode)
        return episode, total_reward, success, total_steps

