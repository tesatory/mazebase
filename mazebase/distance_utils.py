import torch
import time
import os
#TODO remove torch and use a normal python data object for minning



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
            c = c - 10000
        if i.attr.get('_touch_cost'):
            c += i.attr.get('_touch_cost')
    return c

#def score_nhb(game, loc):
#    nhb = get_neighbors(game, loc)
#    for n in nhb:


def path_to_actions(path):
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

def dijkstra_touch_cost(game, source_loc, target_loc):
    W = game.mapsize[0]
    big = 100000
    costs = {}
    dists = torch.ones(game.mapsize[1]*game.mapsize[1])*big
    dists[source_loc[0] + source_loc[1]*W] = 0
    parents = {}
    parents[source_loc] = None
    loc = source_loc
    known = {loc: True}
    while loc != target_loc:
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
        idx = idx[0]
        w = idx % W
        loc = (w, int((idx-w)/W))
    return parents, dists[target_loc[0] + target_loc[1]*W]
