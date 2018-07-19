import mazebase.game_factory as gf
import mazebase.env_wrapper as env_wrapper

def load_config(config_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("module.name", config_path)
    config  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config.game_opts()

def env_maker_all(config_path, args=None):
    game_opts, games, state_feat_class, attr_feat_class = load_config(config_path)
    F = gf.GameFactory(None, None, None)
    for g in games:
        F += games[g].Factory(g, game_opts[g], games[g].Game)
    attr_featurizer = attr_feat_class(game_opts['featurizer'], F.dictionary)
    state_featurizer = state_feat_class(game_opts['featurizer'], F.dictionary)
    return env_wrapper.MazeBaseWrapper(F, state_featurizer, args), F, attr_featurizer, state_featurizer

def env_maker():
    env, _, _ = env_maker_all()
    return env


