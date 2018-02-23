import mazebase.game_factory as gf
import mazebase.goto as goto
import mazebase.switches as switches

def game_opts():
    games = {}
    opts = {}
    opts['featurizer'] = {}
#    opts['featurizer']['abs_loc_vocab'] = True
    shared_static_opts = {}
    shared_static_opts['step_cost'] = -.1
    shared_static_opts['water_cost'] = -.2

    #####################################
    # goto:
    go_dict = {}
    for i in shared_static_opts:
        go_dict[i] = shared_static_opts[i]
    go_dict['fixed_goal'] = True
    go_dict['map_width'] = [5, 10, 5, 10, 1]
    go_dict['map_height'] = [5, 10, 5, 10, 1]
    go_dict['nblocks'] = [1, 5, 1, 5, 1]
    go_dict['nwater'] = [1, 5, 1, 5, 1]
    goto_opts = {'game_opts': gf.opts_from_dict(go_dict),
                'featurizer': opts['featurizer']}
    opts['goto'] = goto_opts
    games['goto'] = goto

    #####################################
    # switches:
    go_dict = {}
    for i in shared_static_opts:
        go_dict[i] = shared_static_opts[i]
    go_dict['map_width'] = [5, 10, 5, 10, 1]
    go_dict['map_height'] = [5, 10, 5, 10, 1]
    go_dict['nblocks'] = [1, 5, 1, 5, 1]
    go_dict['nwater'] = [1, 5, 1, 5, 1]
    go_dict['nswitches'] = [3, 5, 3, 5, 1]
    go_dict['ncolors'] = [3, 3, 3, 3, 0]

    switches_opts = {'game_opts': gf.opts_from_dict(go_dict),
                'featurizer': opts['featurizer']}
    opts['switches'] = switches_opts
    games['switches'] = switches

    ######################################
    #fixme:
    h = 0
    w = 0
    for g in opts:
        h = max(opts[g]['game_opts']['map_height'].max_possible(), h)
        w = max(opts[g]['game_opts']['map_width'].max_possible(), w)
    opts['featurizer']['max_map_sizes'] = (w,h)
    return game_opts, games
