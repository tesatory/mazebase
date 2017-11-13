from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import types
import random

import mazebase.standard_grid_actions

# an item in its simplest form is defined
# by the dictionary attr.
# attr['loc'] if it exists gives the location
#   of the item on the grid as a 2-tuple


class grid_item():
    def __init__(self,attr):
        self.attr = attr
        #for visualization
        self.PRIO = 0
        self.drawme = True

    def is_reachable(self):
        return self.attr.get('_reachable') or self.attr.get('_immaterial') or False

    def update(self,game):
        pass

    def _get_display_symbol(self):
        s = self.attr.get('_display_symbol')
        if s is not None:
            return s
        else:
            return (u'   ', None, None, None)

    #todo more refined to_sentence()
    #maybe attr classes with their own stringifiers?
    #direct to_tensor()?
    def to_sentence(self):
        s = []
        for i in self.attr:
            if i == 'loc':
                loc = self.attr[i]
                # it is up to the featurizer to implement egocentric coords!
                s.append('loc_x'+str(loc[0])+'y'+str(loc[1]))
            elif i[0] != '_' :
                if i[0] != '@':
                    s.append(i)
                else:
                    s.append(self.attr[i])
        return s

    #TODO clone() and change_owner()



class grid_agent(grid_item):
    def __init__(self, attr, actions = None):
        super(grid_agent, self).__init__(attr)
        self.actions = {}
        self.game = None
        # actions = None gives default set of movement actions
        # to build an empty agent, use actions = {}
        if actions is None:
            self.replace_action('up', standard_grid_actions.up)
            self.replace_action('down', standard_grid_actions.down)
            self.replace_action('left', standard_grid_actions.left)
            self.replace_action('right', standard_grid_actions.right)
            self.replace_action('stop', standard_grid_actions.stop)
        else:
            for i in actions:
                self.replace_action(i, actions[i])

    def at_itemtype(self,itemtype):
        if self.game == None:
            return False
        items = self.game.items_byloc(self.attr.loc)
        for i in items:
            if i.attr['_type'] == itemtype:
                return True

    def touch_cost(self):
        c = 0
        if self.game == None:
            return 0
        items = self.game.items_byloc[self.attr['loc']]
        for i in items:
            if i.attr.get('_touch_cost'):
                c += i.attr.get('_touch_cost')
        return c

    def replace_action(self,name, action):
        self.actions[name] = action.__get__(self)

    def act(self, action_name):
        a = self.actions.get(action_name)
        if a is not None:
            a()

    #TODO symbol depends on agent id
    def _get_display_symbol(self):
        return (u' A ', None, None, None)





def add_agent(game,name = None, actions = None):
    if name is None:
        agents = game.items_bytype.get('agent')
        if agents == None:
            n = 0
        else:
            n = len(agents)
        name = 'agent' + str(n)
    loc = game.get_reachable_loc()
    attr = {'_type':'agent', '@type':'agent',
            '@name':name, '_name':name}
    attr['loc'] = loc
    e = grid_agent(attr, actions = actions)
    e.game = game
    game.add_prebuilt_item(e)





#todo switches with visible number of states?
class cycle_switch(grid_item):
    def __init__(self,attr):
        super(cycle_switch, self).__init__(attr)
        assert(attr.get('_ncolors') is not None)
        self.ncolors = attr['_ncolors']
        self.setc(random.randint(0,attr['_ncolors']-1))
        self.attr['_type'] = 'cycle_switch'
        self.attr['@type'] = 'cycle_switch'
        self.attr['_reachable'] = True
    def toggle(self):
        self.color = (self.color+1) % self.ncolors
        self.attr['@color'] = 'color' + str(self.color)
    def setc(self, color):
        self.color = color % self.ncolors
        self.attr['@color'] = 'color' + str(self.color)
    def _get_display_symbol(self):
        colors = []
        colors.append('on_grey')
        colors.append('on_red')
        colors.append('on_green')
        colors.append('on_yellow')
        colors.append('on_blue')
        colors.append('on_magenta')
        colors.append('on_cyan')
        colors.append('on_white')
        return (u' S ', None, colors[self.color%8], None)


def add_cycle_switch(game, loc, ncolors):
    attr = {'_type':'cycle_switch','_ncolors':ncolors,'loc':loc}
    switch = cycle_switch(attr)
    game.add_prebuilt_item(switch)


def add_corners(game):
    attr = {'_type':'corner','_immaterial':True,'corner':0}
    game.build_add_item(attr, loc = (0,0))
    game.build_add_item(attr, loc = (0,game.mapsize[1]-1))
    game.build_add_item(attr, loc = (game.mapsize[0]-1,0))
    game.build_add_item(attr, loc = (game.mapsize[0]-1,game.mapsize[1]-1))

def build_info_attr(message):
    attr = {'_type':'info','@type':'info'}
    q = message.split()
    count = 0
    for i in q:
        attr[i] = count
        count += 1
    return attr


def add_goal(game,loc,goal_id):
    display_symbol = (u'*{0}*'.format(goal_id), 'red', None, None)
    attr = {'_type':'goal','@type':'goal','@goal':('goal'+str(goal_id)),
            '_display_symbol':display_symbol,'_reachable':True}
    game.build_add_item(attr,loc)


def add_block(game,loc):
    display_symbol = (None, None, 'on_white', None)
    attr = {'_type':'block','@type':'block','_display_symbol':display_symbol}
    game.build_add_item(attr,loc)

def add_water(game,loc):
    cost = game.opts.get('water_cost') or -.1
    display_symbol = (None, None, 'on_blue', None)
    attr = {'_type':'water','@type':'water','_touch_cost':cost,
            '_display_symbol':display_symbol,'_reachable':True}
    game.build_add_item(attr,loc)

def add_random_cycle_switches(game,nswitches,ncolors):
    for i in range(nswitches):
        loc = game.get_empty_loc()
        add_cycle_switch(game,loc,ncolors)

def add_random_blocks(game,nblocks):
    for i in range(nblocks):
        loc = game.get_empty_loc()
        add_block(game,loc)

def add_random_water(game,nwater):
    for i in range(nwater):
        loc = game.get_empty_loc()
        add_water(game,loc)

def add_standard_items(game):
    add_corners(game)
    add_random_blocks(game, game.nblocks)
    add_random_water(game, game.nwater)
    add_agent(game)
