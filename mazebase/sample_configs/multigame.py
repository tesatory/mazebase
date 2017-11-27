import mazebase.goto as goto
import mazebase.switches as switches

def game_opts():
    games = {}
    game_opts = {}
    game_opts['featurizer'] = {}
#    game_opts['featurizer']['abs_loc_vocab'] = True
    shared_static_opts = {}
    shared_static_opts['step_cost'] = -.1
    shared_static_opts['water_cost'] = -.2

    #####################################
    # goto:
    go = {}
    static_opts = {}
    for i in shared_static_opts:
        static_opts[i] = shared_static_opts[i]
    go['static'] = static_opts

    range_opts = {}
    range_opts['map_width'] = [5, 10, 5, 10, 1]
    range_opts['map_height'] = [5, 10, 5, 10, 1]
    range_opts['nblocks'] = [1, 5, 1, 5, 1]
    range_opts['nwater'] = [1, 5, 1, 5, 1]
    go['range'] = range_opts

    go['featurizer'] = game_opts['featurizer']

    game_opts['goto'] = go

    games['goto'] = goto

    #####################################
    # switches:
    go = {}
    static_opts = {}
    for i in shared_static_opts:
        static_opts[i] = shared_static_opts[i]
    go['static'] = static_opts

    range_opts = {}
    range_opts['map_width'] = [5, 10, 5, 10, 1]
    range_opts['map_height'] = [5, 10, 5, 10, 1]
    range_opts['nblocks'] = [1, 5, 1, 5, 1]
    range_opts['nwater'] = [1, 5, 1, 5, 1]
    range_opts['nswitches'] = [3, 5, 3, 5, 1]
    range_opts['ncolors'] = [3, 3, 3, 3, 0]
    go['range'] = range_opts

    go['featurizer'] = game_opts['featurizer']

    game_opts['switches'] = go

    games['switches'] = switches

    ######################################
    #fixme:
    h = 0
    w = 0
    for g in game_opts:
        ropts = game_opts[g].get('range')
        if ropts is not None:
            w = max(w,ropts['map_width'][3])
            h = max(w,ropts['map_height'][3])
    game_opts['featurizer']['max_map_sizes'] = (w,h)
    return game_opts, games
