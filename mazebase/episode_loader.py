import networkx as nx
import numpy as np
import torch
import torch.utils.data
from tqdm import tqdm

class DataBuilder:
    def __init__(self, num_data, factory, featurizer, batchifier, args):
        self.args = args
        self.featurizer = featurizer
        self.factory = factory
        self.batchifier = batchifier
        self.batchsize = args.batch_size or 32
        self.num_data = num_data
        self._build(num_data)

    def _build(self, N):
        data = []
        for _i in tqdm(range(N)):
            g = self.factory.init_random_game()
            S = g.get_supervision(self.featurizer)
            for s in S:
                data.append(s)
        self.data = data
        train_ratio = 0.9
        val_start = int(self.num_data * train_ratio)
        training_data = self.data[:val_start]
        self.train_dataset_loader = torch.utils.data.DataLoader(
                    EpisodeSampler(training_data),
                    batch_size=self.args.batch_size,
                    shuffle=True,
                    num_workers=self.args.num_workers)
        test_data = self.data[val_start:]
        self.test_dataset_loader = torch.utils.data.DataLoader(
                    EpisodeSampler(test_data),
                    batch_size=self.args.batch_size,
                    shuffle=False,
                    num_workers=self.args.num_workers)


class EpisodeSampler(torch.utils.data.Dataset):
    ''' Sample graphs and nodes in graph
    '''
    def __init__(self, data, factory):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        state, action = self.data[idx]
        print(action)
        return {'state': state,
                'action': action }

