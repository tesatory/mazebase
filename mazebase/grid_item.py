from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random

import mazebase.standard_grid_actions as standard_grid_actions

_on_colors = []
_on_colors.append('on_grey')
_on_colors.append('on_red')
_on_colors.append('on_green')
_on_colors.append('on_yellow')
_on_colors.append('on_blue')
_on_colors.append('on_magenta')
_on_colors.append('on_cyan')
_on_colors.append('on_white')

_colors = []
_colors.append('grey')
_colors.append('red')
_colors.append('green')
_colors.append('yellow')
_colors.append('blue')
_colors.append('magenta')
_colors.append('cyan')
_colors.append('white')

# an item in its simplest form is defined
# by the dictionary attr.
# attr['loc'] if it exists gives the location
#   of the item on the grid as a 2-tuple
# all items should have an attr['_type']

class GridItem(object):
    def __init__(self, attr):
        if attr.get('_type') is None:
            attr['_type'] = 'unkown_type'
        self.attr = attr
        # for visualization
        self.PRIO = 0
        self.drawme = True

    def is_reachable(self):
        return self.attr.get('_reachable') or self.attr.get(
            '_immaterial') or False

    def update(self, game):
        pass

    def _get_display_symbol(self):
        s = self.attr.get('_display_symbol')
        if s is not None:
            return s
        else:
            return (u'   ', None, None, None)

    # TODO clone() and change_owner()


# ###############################################################################
# agent
# ###############################################################################


class GridAgent(GridItem):
    def __init__(self, attr, actions=None):
        super(GridAgent, self).__init__(attr)
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

    def at_itemtype(self, itemtype):
        if self.game is None:
            return False
        items = self.game.items_byloc(self.attr.loc)
        for i in items:
            if i.attr['_type'] == itemtype:
                return True

    def touch_cost(self):
        c = 0
        if self.game is None:
            return 0
        items = self.game.items_byloc[self.attr['loc']]
        for i in items:
            if i.attr.get('_touch_cost'):
                c += i.attr.get('_touch_cost')
        return c

    def replace_action(self, name, action):
        self.actions[name] = action.__get__(self)

    def act(self, action_name):
        a = self.actions.get(action_name)
        if a is not None:
            a()

    # TODO symbol depends on agent id
    def _get_display_symbol(self):
        s = self.attr.get('_display_symbol')
        if s is not None:
            return s
        else:
            return (u' A ', None, None, None)


def add_agent(game, name=None, actions=None):
    if name is None:
        agents = game.items_bytype.get('agent')
        if agents is None:
            n = 0
        else:
            n = len(agents)
        name = 'agent' + str(n)
    loc = game.sample_reachable_loc()
    attr = {'_type': 'agent', '@type': 'agent', '@name': name, '_name': name}
    attr['loc'] = loc
    e = GridAgent(attr, actions=actions)
    e.game = game
    game.add_prebuilt_item(e)


# ###############################################################################
# cycle switch
# ###############################################################################
# todo switches with visible number of states?
class CycleSwitch(GridItem):
    def __init__(self, attr):
        super(CycleSwitch, self).__init__(attr)
        assert (attr.get('_ncolors') is not None)
        self.ncolors = attr['_ncolors']
        self.setc(random.randint(0, attr['_ncolors'] - 1))
        self.attr['_type'] = 'cycle_switch'
        self.attr['@type'] = 'cycle_switch'
        self.attr['_reachable'] = True

    def toggle(self):
        self.color = (self.color + 1) % self.ncolors
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
        return (u' S ', None, _on_colors[self.color % 8], None)


def add_cycle_switch(game, loc, ncolors):
    attr = {'_type': 'cycle_switch', '_ncolors': ncolors, 'loc': loc}
    switch = CycleSwitch(attr)
    game.add_prebuilt_item(switch)


# ###############################################################################
# pushable block
# ###############################################################################
class PushableBlock(GridItem):
    def __init__(self, attr):
        super(PushableBlock, self).__init__(attr)
        self.attr['_type'] = 'pushable_block'
        self.attr['@type'] = 'pushable_block'
        self.attr['_pushable'] = True
        self.attr['_reachable'] = False

    def _get_display_symbol(self):
        return (u'   ', None, 'on_green', None)


# ###############################################################################
# cycle_switch_opened_door
# ###############################################################################
# todo door superclass?
class CycleSwitchOpenedDoor(GridItem):
    def __init__(self, attr, color=0):
        super(CycleSwitchOpenedDoor, self).__init__(attr)
        self.attr['_type'] = 'cycle_switch_opened_door'
        self.attr['@type'] = 'cycle_switch_opened_door'
        self.attr['@color'] = 'color' + str(color)
        self.attr['_reachable'] = False
        self.color = color
        self.isopen = False

    def setc(self, c):
        self.color = c
        self.attr['@color'] = 'color' + str(c)

    def update(self, game):
        self.isopen = True
        self.attr['_reachable'] = True
        for i in game.items_bytype['cycle_switch']:
            if self.color != i.color:
                self.isopen = False
                self.attr['_reachable'] = False

    def _get_display_symbol(self):
        #        c = "\x1b[1;%dm" % (30 + self.color%8) + '0' + "\x1b[0m"
        if self.isopen:
            return ('   ', None, None, None)
        else:
            return (' 0 ', _colors[self.color % 8], 'on_white', ['bold'])


def add_corners(game):
    attr = {'_type': 'corner', '_immaterial': True, 'corner': 0}
    game.build_add_item(attr.copy(), loc=(0, 0))
    game.build_add_item(attr.copy(), loc=(0, game.mapsize[1] - 1))
    game.build_add_item(attr.copy(), loc=(game.mapsize[0] - 1, 0))
    game.build_add_item(attr.copy(), loc=(game.mapsize[0] - 1, game.mapsize[1] - 1))


def build_info_attr(message):
    attr = {'_type': 'info', '@type': 'info'}
    q = message.split()
    count = 0
    for i in q:
        attr[i] = count
        count += 1
    return attr


def add_goal(game, loc, goal_id):
    display_symbol = (u'*{0}*'.format(goal_id), 'red', None, None)
    attr = {
        '_type': 'goal',
        '@type': 'goal',
        '@goal': ('goal' + str(goal_id)),
        '_display_symbol': display_symbol,
        '_reachable': True
    }
    game.build_add_item(attr, loc)


def add_block(game, loc):
    display_symbol = (None, None, 'on_white', None)
    attr = {
        '_type': 'block',
        '@type': 'block',
        '_display_symbol': display_symbol
    }
    game.build_add_item(attr, loc)


def add_water(game, loc):
    cost = game.opts.get('water_cost') or -.1
    display_symbol = (None, None, 'on_blue', None)
    attr = {
        '_type': 'water',
        '@type': 'water',
        '_touch_cost': cost,
        '_display_symbol': display_symbol,
        '_reachable': True
    }
    game.build_add_item(attr, loc)


def add_random_cycle_switches(game, nswitches, ncolors):
    for i in range(nswitches):
        loc = game.sample_reachable_loc(ensure_empty=True)
        add_cycle_switch(game, loc, ncolors)


def add_random_blocks(game, nblocks):
    for i in range(nblocks):
        loc = game.sample_reachable_loc(ensure_empty=True)
        add_block(game, loc)


def add_random_water(game, nwater):
    for i in range(nwater):
        loc = game.sample_reachable_loc(ensure_empty=True)
        add_water(game, loc)


def add_standard_items(game):
    add_corners(game)
    add_random_blocks(game, game.nblocks)
    add_random_water(game, game.nwater)
    add_agent(game)


# probably should do this before doing anything else...
def build_big_random_wall(game, orientation='random'):
    if orientation == 'random':
        orientation = 'vertical'
        if random.random() > .5:
            orientation = 'horizontal'
    if orientation == 'vertical':
        w = random.randint(2, game.mapsize[0] - 2)
        for h in range(game.mapsize[1]):
            add_block(game, (w, h))
    else:
        h = random.randint(2, game.mapsize[1] - 2)
        for w in range(game.mapsize[0]):
            add_block(game, (w, h))
