import torch
import torch.multiprocessing as mp
import sys
if sys.version_info[0] == 2:
    import Queue
else:
    import queue as Queue

def share_memory(ep):
    for item in ep:
        tp = type(item)
        if tp == list:
            share_memory(item)
        elif torch.is_tensor(item):
            item.share_memory_()

class ThreadedWorker(mp.Process):
    def __init__(self, runner_maker, queue, done, stop_queueing, *args, **kwargs):
        super(ThreadedWorker, self).__init__(*args, **kwargs)
        self.episode_runner = runner_maker()
        self.queue = queue
        self.done_flag = done
        self.stop_queueing = stop_queueing

    def run(self):
        while True:
            if self.done_flag.is_set():
                return
            if not self.stop_queueing.is_set():
                episode = self.episode_runner.get_episode()
                share_memory(episode)
                self.queue.put(episode)


class ThreadedEpisodeRunner(object):
    def __init__(self, args, runner_maker):
        self.state_queues = []
        self.prev = []
        self.episodes = []
        self.stop_queueing = mp.Event()
        self.done = mp.Event()
        self.stop_queueing.clear()
        self.done.clear()
        self.num = args.nthreads
        self.processes = []
        for i in range(self.num):
            # queue size of 1 seems to be pretty ideal, longer queue and the resetting takes time
            queue = mp.Queue(1)
            self.state_queues.append(queue)
            self.prev.append(None)
            self.episodes.append([])
            worker = ThreadedWorker(runner_maker, queue, self.done, self.stop_queueing)
            worker.start()
            self.processes.append(worker)
        self.args = args
        runner_temp = runner_maker()
        self.policy_net = runner_temp.policy_net
        self.value_net = runner_temp.value_net


    def quit(self):
        self.done.set()
        while any(x.is_alive() for x in self.processes):
            for queue in self.state_queues:
                if not queue.empty():
                    return queue.get()

    def reset(self):
        self.stop_queueing.set()
        for r in self.state_queues:
            while not r.empty():
                r.get()
        self.stop_queueing.clear()


    def get_episode(self):
        while True:
            for queue in self.state_queues:
                try:
                    episode = queue.get(False)
                    return episode
                except Queue.Empty:
                    pass
