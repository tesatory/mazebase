import mazebase.game_factory as gf
import mazebase.switches as switches
from mazebase.torch_featurizers import GridFeaturizer
from mazebase.torch_featurizers import ObjFeaturizer

def game_opts():
    #featurizer_class = GridFeaturizer
    featurizer_class = ObjFeaturizer
    games = {}
    opts = {}
    opts['featurizer'] = {}
    shared_static_opts = {}
    shared_static_opts['step_cost'] = -.1
    shared_static_opts['water_cost'] = -.2

    #####################################
    # switches:
    switch_dict = {}
    for i in shared_static_opts:
        switch_dict[i] = shared_static_opts[i]
    switch_dict['fixed_goal'] = True
    switch_dict['map_width'] = [5, 5, 5, 5, 0]
    switch_dict['map_height'] = [5, 5, 5, 5, 0]
    switch_dict['nblocks'] = [2, 2, 2, 2, 0]
    switch_dict['nwater'] = [1, 1, 1, 1, 0]
    switch_dict['nswitches'] = [2, 2, 2, 2, 0]
    switch_dict['ncolors'] = [2, 2, 2, 2, 0]

    switches_opts = {'game_opts': gf.opts_from_dict(switch_dict),
                'featurizer': opts['featurizer']}
    opts['switches'] = switches_opts
    games['switches'] = switches
    
    #fixme:
    h = opts['switches']['game_opts']['map_height'].max_possible()
    w = opts['switches']['game_opts']['map_width'].max_possible()
    opts['featurizer']['max_map_sizes'] = (w,h)
    
    return opts, games, featurizer_class

