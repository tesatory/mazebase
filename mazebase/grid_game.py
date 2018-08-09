from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random
import os

import mazebase.grid_item as gi
from mazebase.util.termcolor import cprint


# the factory collects the vocab...
# the factory holds the mapping from indices to actions
#     common for all agents
# TODO .step()


class GridGame2D(object):
    def __init__(self, opts):
        self.t = 0
        self.opts = opts
        self.items = []
        self.items_bytype = {}
        self.items_byname = {}
        self.items_byloc = {}
        self.mapsize = (opts['map_width'], opts['map_height'])
        self.finished = False
        self.agent = None


    def sample_loc(self, fat):
        x = random.randint(fat, self.mapsize[0] - fat - 1)
        y = random.randint(fat, self.mapsize[1] - fat - 1)
        return (x, y)

    def is_loc_reachable(self, loc):
        x, y = loc
        if (x < 0 or y < 0 or x >= self.mapsize[0] or y >= self.mapsize[1]):
            return False
        loc_items = self.items_byloc.get(loc, [])
        return all(i.is_reachable() for i in loc_items)

    def is_loc_empty(self, loc):
        x, y = loc
        loc_items = self.items_byloc.get(loc, [])
        return all(i.attr.get('_immaterial') for i in loc_items)

    def sample_reachable_loc(self, fat=0, ensure_empty=False):
        for i in range(100):
            loc = self.sample_loc(fat)
            if self.is_loc_reachable(loc):
                if not ensure_empty:
                    return loc
                if self.is_loc_empty(loc):
                    return loc
        raise RuntimeError(
            "Failed to find reachable location after 100 tries! Your map"
            "size is probably too small")

    # Do not change attr['_type'] by hand.  always use:
    def retype_item(self, item, newtype):
        # TODO clean up len 0 lists?
        assert (item in self.items)
        oldtype = item.attr['_type']
        item.attr['_type'] = newtype
        self.items_bytype[oldtype].remove(item)
        if self.items_bytype.get(newtype) is None:
            self.items_bytype[newtype] = []
        self.items_bytype[newtype].append(item)

    # Do not change attr['loc'] by hand.  always use:
    def move_item(self, item, loc):
        # TODO error if target loc is outside of map
        # TODO clean up len 0 lists?
        assert (item in self.items)
        oldloc = item.attr.get('loc')
        if oldloc is not None:
            item.attr['loc'] = loc
            self.items_byloc[oldloc].remove(item)
            if self.items_byloc.get(loc) is None:
                self.items_byloc[loc] = []
            self.items_byloc[loc].append(item)
        else:
            raise RuntimeError("Tried to move an item with no location")

    # Do not change attr['name'] by hand.  always use:
    def rename_item(self, item, newname):
        # TODO clean up len 0 lists?
        assert (item in self.items)
        assert (self.items_byname.get(newname)) is None
        oldname = item.attr.get('_name')
        if oldname is not None:
            item.attr['_name'] = newname
            self.items_byname.remove(item)
        self.items_byname[newname] = item

    def remove_item(self, item):
        assert (item in self.items)
        loc = item.attr.get('loc')
        if loc is not None:
            self.items_byloc[loc].remove(item)
        item_name = item.attr.get('_name')
        if item_name is not None:
            del self.items_byname[item_name]
        item_type = item.attr.get('_type')
        if item_type is not None:
            self.items_bytype[item_type].remove(item)

        self.items.remove(item)

    def add_prebuilt_item(self, item):
        self.items.append(item)
        loc = item.attr.get('loc')
        if loc is not None:
            if self.items_byloc.get(loc) is None:
                self.items_byloc[loc] = []
            self.items_byloc.get(loc).append(item)
        if item.attr.get('_name') is not None:
            # names should be unique.
            self.items_byname[item.attr.get('_name')] = item
        item_type = item.attr.get('_type')
        if self.items_bytype.get(item_type) is None:
            self.items_bytype[item_type] = []
        self.items_bytype.get(item_type).append(item)

    def build_add_item(self, attr, loc=''):
        if loc == 'random_empty':
            attr['loc'] = self.sample_reachable_loc(ensure_empty=True)
        elif loc == 'random_reachable':
            attr['loc'] = self.sample_reachable_loc()
        elif loc == 'random':
            attr['loc'] = self.sample_loc()
        elif loc == '':
            pass
        else:
            attr['loc'] = loc

        if attr.get('_factory') is not None:
            e = attr.get('_factory')(attr, self)
        else:
            e = gi.GridItem(attr)
        self.add_prebuilt_item(e)
        return e

    def update(self):
        for i in self.items:
            i.update(self)
        self.t = self.t + 1

    def is_active(self):
        return not self.finished

    # fixme?
    def is_success(self):
        if self.is_active():
            return False
        return True

    def get_reward(self, agent=None):
        return 0

    def act(self, action, agent=0):
        self.items_bytype['agent'][agent].act(action)

    def interactive_ascii(self):
        self.display_ascii()
        while self.is_active():
            a = input()
            os.system('clear')
            if self.agent:
                self.agent.act(a)
            self.update()
            self.display_ascii()
            print(self.get_reward())

    def display_ascii(self):
        width = self.mapsize[0]
        height = self.mapsize[1]
        ''' Displays the game map for visualization '''
        if 'info' in self.items_bytype:
            for i in self.items_bytype['info']:
                words = {k: v for k, v in i.attr.items() if type(v) == int}
                swords = sorted(words, key=words.get)
                print(' '.join(swords))
        cprint(' ' * (width + 2) * 3, None, 'on_white')
        for y in reversed(range(height)):
            cprint(str(y).center(3), 'red', 'on_white', end="")
            for x in range(width):
                items = self.items_byloc.get((x, y))
                disp = [u'   ', None, None, None]
                if items is not None and len(items) > 0:
                    itemlst = sorted(
                        filter(lambda x: x.drawme, items),
                        key=lambda x: x.PRIO)
                    for item in itemlst:
                        if item.attr.get('_invisible'):
                            continue
                        config = item._get_display_symbol()
                        for i, v in list(enumerate(config))[1:]:
                            if v is not None:
                                disp[i] = v
                        s = config[0]
                        if s is None:
                            continue
                        d = list(disp[0])
                        for i, char in enumerate(s):
                            if char != ' ':
                                d[i] = char
                        disp[0] = "".join(d)
                text, color, bg, attrs = disp
                cprint(text, color, bg, attrs, end="")
            cprint('   ', None, 'on_white')
        cprint('   ', None, 'on_white', end="")
        for s in range(width):
            cprint(str(s).center(3), 'red', 'on_white', end="")
        cprint('   ', None, 'on_white')
