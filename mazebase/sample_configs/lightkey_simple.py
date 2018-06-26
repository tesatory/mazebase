import mazebase.game_factory as gf
import mazebase.lightkey as lightkey
from mazebase.torch_featurizers import GridFeaturizer
from mazebase.torch_featurizers import ObjFeaturizer

def game_opts():
    featurizer_class = GridFeaturizer
    #featurizer_class = ObjFeaturizer
    games = {}
    opts = {}
    opts['featurizer'] = {}
    shared_static_opts = {}
    shared_static_opts['step_cost'] = -.1
    shared_static_opts['water_cost'] = -.2

    #####################################
    # cond:
    g_dict = {}
    for i in shared_static_opts:
        g_dict[i] = shared_static_opts[i]
    g_dict['fixed_goal'] = True
    g_dict['map_width'] = [7, 7, 7, 7, 0]
    g_dict['map_height'] = [7, 7, 7, 7, 0]
    g_dict['nblocks'] = [2, 2, 2, 2, 0]
    g_dict['nwater'] = [1, 1, 1, 1, 0]
    g_dict['nswitches'] = [2, 2, 2, 2, 0]
    g_dict['ncolors'] = [2, 2, 2, 2, 0]

    g_opts = {'game_opts': gf.opts_from_dict(g_dict),
                'featurizer': opts['featurizer']}
    opts['lightkey'] = g_opts
    games['lightkey'] = lightkey

    #fixme:
    h = opts['lightkey']['game_opts']['map_height'].max_possible()
    w = opts['lightkey']['game_opts']['map_width'].max_possible()
    opts['featurizer']['max_map_sizes'] = (w,h)

    return opts, games, featurizer_class

