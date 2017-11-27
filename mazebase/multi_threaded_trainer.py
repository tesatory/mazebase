import torch.multiprocessing as mp

class ThreadedWorker(mp.Process):
    def __init__(self, runner_maker, state_send, done, test, *args, **kwargs):
        super(ThreadedWorker, self).__init__(*args, **kwargs)
        self.episode_runner = runner_maker()
#        self.episode_runner.test = test
        self.send = state_send
        self.done_flag = done

    def run(self):
        while True:
            if self.done_flag.is_set():
                return
            episode = self.episode_runner.get_episode()
            self.send.send(episode)
            

class ThreadedEpisodeRunner(object):
    def __init__(self, args, runner_maker):
        self.eps_queue = mp.Queue()
        self.state_listeners = []
        self.prev = []
        self.episodes = []
        self.done = mp.Event()
 #       self.test = mp.Event()
        self.done.clear()
#        self.test.clear()
        self.num = args.nthreads
#        n_testers = self.num * args.sp_test_rate
        self.processes = []
        for i in range(self.num):
            state_recv, state_send = mp.Pipe()
            self.state_listeners.append(state_recv)
            self.prev.append(None)
            self.episodes.append([])
            worker = ThreadedWorker(runner_maker, state_send, self.done, self.done)
            worker.start()
            self.processes.append(worker)
        self.args = args
        runner_temp = runner_maker()
        self.policy_net = runner_temp.policy_net
        self.value_net = runner_temp.value_net

    def quit(self):
        self.done.set()
        while any(x.is_alive() for x in self.processes):
            for listener in self.state_listeners:
                if listener.poll():
                    return listener.recv()

    def reset(self):
        for r in self.state_listeners:
            while r.poll():
                r.recv()

    def get_episode(self):
        while True:
            for listener in self.state_listeners:
                if listener.poll():
                    return listener.recv()
