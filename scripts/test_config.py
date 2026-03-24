# test_config.py
from scripts.config_loader import load_global_config, get_all_configs

config = load_global_config()
print("Global config:", config)

all_configs = get_all_configs()
print("All configs keys:", list(all_configs.keys()))
print("Organization:", all_configs["global"].get("organization"))
print(all_configs)