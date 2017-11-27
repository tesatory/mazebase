import time
class Timer:    
    def __init__(self, msg, sync=False):
        self.msg = msg
        self.sync = sync

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start
        print("{}: {} s".format(self.msg, self.interval))
