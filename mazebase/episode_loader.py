import networkx as nx
import numpy as np
import torch
import torch.utils.data
from tqdm import tqdm


class EpisodeSampler(torch.utils.data.Dataset):
    ''' Sample state/action
    '''
    def __init__(self, data, factory):
        self.data = data
        self.factory = factory

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        state, action = self.data[idx]
        if isinstance(state, list):
            state[0] = state[0].double()
        return {'state': state,
                'action': torch.LongTensor([self.factory.actions[action]]) }


class DataBuilder:
    def __init__(self, num_epi, factory, featurizer, batchifier, args, sampler=EpisodeSampler, train_ratio=0.9):
        self.args = args
        self.featurizer = featurizer
        self.factory = factory
        self.batchifier = batchifier
        self.batchsize = args.batch_size or 32
        self.num_epi = num_epi
        self.sampler = sampler
        self._build(num_epi)
        self.train_ratio = train_ratio

    def _build(self, N):
        self.data = self.supervision_data(N)
        val_start = int(len(self.data) * self.train_ratio)
        training_data = self.data[:val_start]
        self.train_dataset_loader = torch.utils.data.DataLoader(
                    self.sampler(training_data, self.factory),
                    batch_size=self.batchsize,
                    shuffle=True,
                    num_workers=self.args.num_workers)
        test_data = self.data[val_start:]
        self.test_dataset_loader = torch.utils.data.DataLoader(
                    self.sampler(test_data, self.factory),
                    batch_size=self.batchsize,
                    shuffle=True,
                    num_workers=self.args.num_workers)

    def supervision_data(self, N):
        # data: a list of state-action pairs
        data = []
        for _i in tqdm(range(N)):
            g = self.factory.init_random_game()
            S = g.get_supervision(self.featurizer)
            for s in S:
                data.append(s)
        return data


