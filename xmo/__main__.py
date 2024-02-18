import os
import xmo.dns
import xmo.dmz
import xmo.log
import xmo.mode
import xmo.wifi
import yaml
from . import xmo


def main():
    config = dict()
    config_path = os.path.join(os.getcwd(), 'config.yaml')
    if os.path.isfile(config_path):
        with open(config_path) as f:
            config = yaml.safe_load(f)
    xmo.cli(default_map=config, _anyio_backend='asyncio')


if __name__ == '__main__':
    main()
