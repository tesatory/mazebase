from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
import random
import grid_item as gi
import os
from termcolor import cprint



def format_number(s):
    if s<10:
        ss = ' ' + str(s)  + ' '
    elif s<100:   
        ss = ' ' + str(s)
    else:
        ss = str(s)
    return ss
         
#the factory collects the vocab...
#the factory holds the featurizer
#the factory holds the mapping from indices to actions
#     common for all agents
#TODO .step()

class grid_game_2d():
    def __init__(self, opts):
        self.t = 0
        self.opts = opts
        self.items = []
        self.items_bytype = {}
        self.items_byname = {}
        self.items_byloc = {}
        self.mapsize = (opts['map_width'],opts['map_height'])
        self.finished = False
        self.agent = None

    def is_loc_reachable(self,loc):
        if loc[0]<0 or loc[1]<0:
            return False
        if loc[0]>=self.mapsize[0] or loc[0]>=self.mapsize[1]:
            return False
        reachable = True
        loc_items = self.items_byloc.get(loc)
        if loc_items is not None:
            for i in loc_items:
                reachable = reachable and i.is_reachable()
        return reachable

#    def is_loc_visible(loc):

    def random_loc(self, fat):
        x = random.randint(fat, self.mapsize[0]-fat-1)
        y = random.randint(fat, self.mapsize[1]-fat-1)
        return (x,y)

#TODO merge these
    def get_reachable_loc(self,fat = 0):
        for i in range(100):
            loc = self.random_loc(fat)
            reachable = True
            items = self.items_byloc.get(loc)
            if items is not None:
                for i in items:
                    reachable = reachable and i.is_reachable()
            if reachable:
                return loc
        raise RuntimeError("Failed to find reachable location after 100 tries! Your map"
                           "size is probably too small")

    def get_empty_loc(self,fat = 0):
        for i in range(100):
            loc = self.random_loc(fat)
            empty = True
            items = self.items_byloc.get(loc)
            if items is not None:
                for i in items:
                    if not i.attr.get('_immaterial'):
                        empty = False
            if empty:
                return loc

        raise RuntimeError("Failed to find empty location after 100 tries! Your map"
                           "size is probably too small")

    def move_item(self, item, loc):
        #TODO error if target loc is outside of map
        #TODO clean up len 0 lists?
        assert(item in self.items)
        oldloc = item.attr.get('loc')
        if oldloc is not None:
            item.attr['loc'] = loc
            self.items_byloc[oldloc].remove(item)
            if self.items_byloc.get(loc) is None:
                self.items_byloc[loc] = []
            self.items_byloc[loc].append(item)
        else:
            raise RuntimeError("Tried to move an item with no location")

    def remove_item(self,item):
        assert(item in self.items)
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
            #names should be unique.
            self.items_byname[item.attr.get('_name')] = item
        item_type = item.attr.get('_type')
        if item_type is not None:
            if self.items_bytype.get(item_type) is None:
                self.items_bytype[item_type] = []
            self.items_bytype.get(item_type).append(item)

    def build_add_item(self,attr, loc = ''):
        if loc == 'random_empty':
            attr['loc'] = self.get_empty_loc()
        elif loc == 'random_reachable':
            attr['loc'] = self.get_reachable_loc()
        elif loc == 'random':
            attr['loc'] = self.random_loc()
        elif loc == '':
            pass
        else:
            attr['loc'] = loc

        if attr.get('_factory') is not None:
            e = attr.get('_factory')(attr, self)
        else:
            e = gi.grid_item(attr)
        self.add_prebuilt_item(e)
        return e

    def update(self):
        for i in self.items:
            i.update(self)
        self.t = self.t + 1

    def is_active(self):
        return not self.finished

    #fixme?
    def is_success(self):
        if self.is_active():
            return False
        return True

    def get_reward(self, agent = None):
        return 0

    def act(self,action, agent = 0):
        self.items_bytype['agent'][agent].act(action)

    def to_sentence(self):
        s = []
        for i in self.items:
            s.append(i.to_sentence())
        return s
        
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
        for i in self.items_bytype['info']:
            words = {k: v for k, v in i.attr.items() if type(v)==int}
            swords = sorted(words, key = words.get)
            print(' '.join(swords))
        cprint(' ' * (width + 2) * 3, None, 'on_white')
        for y in reversed(range(height)):
            cprint(format_number(y), 'red', 'on_white', end ="")
            for x in range(width):
                items = self.items_byloc.get((x,y))
                disp = [u'   ', None, None, None]
                if items is not None and len(items)>0:
                    itemlst = sorted(filter(lambda x: x.drawme, items),
                                 key=lambda x: x.PRIO)
                    for item in itemlst:
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
        cprint('   ', None, 'on_white',end ="")
        for s in range(width):
            cprint(format_number(s), 'red', 'on_white', end ="")
        cprint('   ', None, 'on_white')
