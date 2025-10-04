import os
import yaml

import xmo.dns
import xmo.dmz
import xmo.log
import xmo.mode
import xmo.wifi

from . import xmo


def main():
    config = {}
    config_path = os.path.join(os.getcwd(), 'config.yaml')
    if os.path.isfile(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    xmo.cli(default_map=config, _anyio_backend='asyncio')


if __name__ == '__main__':
    main()
    