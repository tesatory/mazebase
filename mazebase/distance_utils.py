import torch
import time
import os
#TODO remove torch and use a normal python data object for minning

__BIG_COST = 100000

def get_big_cost():
    return __BIG_COST

def get_neighbors(game, loc):
    n = []
    if loc[0] > 0:
        n.append((loc[0]-1, loc[1]))
    if loc[1] > 0:
        n.append((loc[0], loc[1]-1))
    if loc[0] < game.mapsize[0]-1:
        n.append((loc[0] + 1, loc[1]))
    if loc[1] < game.mapsize[1]-1:
        n.append((loc[0], loc[1] + 1))
    return n

def score_loc(game, loc):
    items = game.items_byloc.get(loc)
    c = game.opts['step_cost']
    if items is None:
        return c
    for i in items:
        if not game.is_loc_reachable(loc):
            c = c - __BIG_COST
        if i.attr.get('_touch_cost'):
            c += i.attr.get('_touch_cost')
    return c

#def score_nhb(game, loc):
#    nhb = get_neighbors(game, loc)
#    for n in nhb:


def path_to_actions(path):
    if len(path) == 0:
        return []
    p = path[0]
    actions = []
    for i in range(len(path)-1):
        loc = path[i + 1]
        if p[0] < loc[0]:
            actions.append('right')
        elif p[1] < loc[1]:
            actions.append('up')
        elif p[0] > loc[0]:
            actions.append('left')
        elif p[1] > loc[1]:
            actions.append('down')
        else:
            wtf
        p = loc
    return actions


def collect_path(parents, target_loc):
    if parents is None:
        return []
    loc = target_loc
    path = [loc]
    while parents[loc] is not None:
        loc = parents[loc]
        path.append(loc)
    path.reverse()
    return path

def search_and_move(game, target_loc, display = False):
    p, _ = dijkstra_touch_cost(game, game.agent.attr['loc'], target_loc)
    path = collect_path(p, target_loc)
    actions = path_to_actions(path)
    for a in actions:
        game.act(a)
        game.update()
        if display:
            time.sleep(.2)
            os.system('clear')
            game.display_ascii()
    return p, path, actions

def dijkstra_touch_cost_all(game, source_loc):
    W = game.mapsize[0]
    big = 100*__BIG_COST
    costs = {}
    # hacky atm. dists[loc] for visited location will be set to BIG_COST such that
    # dists.min resembles the behavior of the priority queue in standard dijkstra.
    dists = torch.ones(game.mapsize[0]*game.mapsize[1])*big
    d = torch.ones(game.mapsize[0]*game.mapsize[1])*big
    dists[source_loc[0] + source_loc[1]*W] = 0
    d[source_loc[0] + source_loc[1]*W] = 0
    parents = {}
    parents[source_loc] = None
    loc = source_loc
    known = {loc: True}
    tcount = 0
    while len(known) < len(dists):
        tcount += 1
        if tcount > 2000:
            import pdb
            pdb.set_trace()
        nhb = get_neighbors(game, loc)
        for n in nhb:
            if costs.get(n) is None:
                costs[n] = -score_loc(game, n)
            if not known.get(n):
                if dists[n[0] + n[1]*W] > costs[n] + dists[loc[0] + loc[1]*W]:
                    dists[n[0] + n[1]*W] = costs[n] + dists[loc[0] + loc[1]*W]
                    d[n[0] + n[1]*W] = dists[n[0] + n[1] * W]
                    parents[n] = loc

        dists[loc[0] + loc[1]*W] = big
        known[loc] = True
        val, idx = dists.min(0)
        #idx = idx[0]  # deprecated: for pytorch 0.3
        idx = idx.item()
        w = idx % W
        loc = (w, int((idx-w)/W))
    return parents, d


def dijkstra_touch_cost(game, source_loc, target_loc):
    if not game.is_loc_reachable(target_loc):
        return None, __BIG_COST
    W = game.mapsize[0]
    big = 100*__BIG_COST
    costs = {}
    dists = torch.ones(game.mapsize[0]*game.mapsize[1])*big
    dists[source_loc[0] + source_loc[1]*W] = 0
    parents = {}
    parents[source_loc] = None
    loc = source_loc
    known = {loc: True}
    tcount = 0
    while loc != target_loc:
        tcount += 1
        if tcount > 2000:
            import pdb
            pdb.set_trace()
        nhb = get_neighbors(game, loc)
        for n in nhb:
            if costs.get(n) is None:
                costs[n] = -score_loc(game, n)
            if not known.get(n):
                if dists[n[0] + n[1]*W] > costs[n] + dists[loc[0] + loc[1]*W]:
                    dists[n[0] + n[1]*W] = costs[n] + dists[loc[0] + loc[1]*W]
                    parents[n] = loc

        dists[loc[0] + loc[1]*W] = big
        known[loc] = True
        val, idx = dists.min(0)
        #idx = idx[0]  # deprecated: for pytorch 0.3
        idx = idx.item()
        w = idx % W
        loc = (w, int((idx-w)/W))

    return parents, dists[target_loc[0] + target_loc[1]*W]

def all_reachable_locs(game, source_loc, empty=True):
    reachable_locs = []
    parents, dists = dijkstra_touch_cost_all(game, source_loc)
    W = game.mapsize[0]
    H = game.mapsize[1]
    for i in range(W):
        for j in range(H):
            if dists[i + j * W] < __BIG_COST and game.is_loc_reachable((i,j)):
                if empty and not game.is_loc_empty((i, j)):
                    continue
                reachable_locs.append((i, j))
    return reachable_locs

