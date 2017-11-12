from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import types
import random


def up(agent):
    w = agent.attr['loc'][0]
    h = agent.attr['loc'][1]
    target = (w,h+1)
    if agent.game.is_loc_reachable(target):
        agent.game.move_item(agent,target)

def down(agent):
    w = agent.attr['loc'][0]
    h = agent.attr['loc'][1]
    target = (w,h-1)
    if agent.game.is_loc_reachable(target):
        agent.game.move_item(agent,target)

def left(agent):
    w = agent.attr['loc'][0]
    h = agent.attr['loc'][1]
    target = (w-1,h)
    if agent.game.is_loc_reachable(target):
        agent.game.move_item(agent,target)

def right(agent):
    w = agent.attr['loc'][0]
    h = agent.attr['loc'][1]
    target = (w+1,h)
    if agent.game.is_loc_reachable(target):
        agent.game.move_item(agent,target)

def stop(agent):
    pass


#this will toggle all items with a toggle method
#that are at the same location as the agent
def toggle_close(agent):
    items = agent.game.items_byloc[agent.attr['loc']]
    for i in items:
        toggle = getattr(i,"toggle", None)
        if callable(toggle):
            i.toggle()
