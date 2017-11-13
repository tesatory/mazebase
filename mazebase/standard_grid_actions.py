from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import types
import random


def up(agent):
    w = agent.attr['loc'][0]
    h = agent.attr['loc'][1]
    target = (w, h + 1)
    if agent.game.is_loc_reachable(target):
        agent.game.move_item(agent, target)


def down(agent):
    w = agent.attr['loc'][0]
    h = agent.attr['loc'][1]
    target = (w, h - 1)
    if agent.game.is_loc_reachable(target):
        agent.game.move_item(agent, target)


def left(agent):
    w = agent.attr['loc'][0]
    h = agent.attr['loc'][1]
    target = (w - 1, h)
    if agent.game.is_loc_reachable(target):
        agent.game.move_item(agent, target)


def right(agent):
    w = agent.attr['loc'][0]
    h = agent.attr['loc'][1]
    target = (w + 1, h)
    if agent.game.is_loc_reachable(target):
        agent.game.move_item(agent, target)


def stop(agent):
    pass


# this will toggle all items with a toggle method
# that are at the same location as the agent
def toggle_close(agent):
    items = agent.game.items_byloc[agent.attr['loc']]
    for i in items:
        toggle = getattr(i, "toggle", None)
        if callable(toggle):
            i.toggle()


def push_item(game, item, target_loc):
    if not game.is_loc_reachable(target_loc):
        pass
    else:
        if item.attr.get('_pushable'):
            game.move_item(item, target_loc)


def push_up(agent):
    w = agent.attr['loc'][0]
    h = agent.attr['loc'][1]
    to_be_pushed_loc = (w, h + 1)
    target_loc = (w, h + 2)
    items = agent.game.items_byloc[to_be_pushed_loc]
    for i in items:
        push_item(agent.game, i, target_loc)


def push_down(agent):
    w = agent.attr['loc'][0]
    h = agent.attr['loc'][1]
    to_be_pushed_loc = (w, h - 1)
    target_loc = (w, h - 2)
    items = agent.game.items_byloc[to_be_pushed_loc]
    for i in items:
        push_item(agent.game, i, target_loc)


def push_left(agent):
    w = agent.attr['loc'][0]
    h = agent.attr['loc'][1]
    to_be_pushed_loc = (w - 1, h)
    target_loc = (w - 2, h)
    items = agent.game.items_byloc[to_be_pushed_loc]
    for i in items:
        push_item(agent.game, i, target_loc)


def push_right(agent):
    w = agent.attr['loc'][0]
    h = agent.attr['loc'][1]
    to_be_pushed_loc = (w + 1, h)
    target_loc = (w + 2, h)
    items = agent.game.items_byloc[to_be_pushed_loc]
    for i in items:
        push_item(agent.game, i, target_loc)
