import mazebase.game_factory as gf
import mazebase.goto as goto
from mazebase.torch_featurizers import SparseSentenceFeaturizer

def game_opts():
    featurizer_class = SparseSentenceFeaturizer
    games = {}
    opts = {}
    opts['featurizer'] = {'egocentric_coordinates':True, 
                               'separate_loc':False,
                               'visible_range':8 }
    shared_static_opts = {}
    shared_static_opts['step_cost'] = -.1
    shared_static_opts['water_cost'] = -.2

    #####################################
    # goto:
        # goto:
    go_dict = {}
    for i in shared_static_opts:
        go_dict[i] = shared_static_opts[i]
    go_dict['fixed_goal'] = True
    go_dict['map_width'] = [5, 10, 1, 10, 1]
    go_dict['map_height'] = [5, 10, 1, 10, 1]
    go_dict['nblocks'] = [1, 1, 1, 5, 1]
    go_dict['nwater'] = [1, 1, 1, 5, 1]
    goto_opts = {'game_opts': gf.opts_from_dict(go_dict),
                'featurizer': opts['featurizer']}
    opts['goto'] = goto_opts
    games['goto'] = goto
    
    #fixme:
    h = opts['goto']['game_opts']['map_height'].max_possible()
    w = opts['goto']['game_opts']['map_width'].max_possible()
    opts['featurizer']['max_map_sizes'] = (w,h)
    
    return opts, games, featurizer_class
