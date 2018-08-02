import mazebase.game_factory as gf
import mazebase.env_wrapper as env_wrapper

def load_config(config_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("module.name", config_path)
    config  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config.game_opts()

def env_maker_all(config_path, args=None):
    configs = load_config(config_path)
    if len(configs) == 3:
        game_opts, games, state_feat_class = configs
    else:
        # when additional (object-oriented) featurizer is needed
        game_opts, games, state_feat_class, attr_feat_class = configs
    F = gf.GameFactory(None, None, None)
    for g in games:
        F += games[g].Factory(g, game_opts[g], games[g].Game)
    state_featurizer = state_feat_class(game_opts['featurizer'], F.dictionary)

    if len(configs) > 3:
        attr_featurizer = attr_feat_class(game_opts['featurizer'], F.dictionary)
        return env_wrapper.MazeBaseWrapper(F, state_featurizer, args), F, attr_featurizer, state_featurizer
    else:
        return env_wrapper.MazeBaseWrapper(F, state_featurizer, args), F, state_featurizer

def env_maker(config_path):
    env, _, _ = env_maker_all(config_path)
    return env


