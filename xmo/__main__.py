import os
import xmo.dns
import xmo.dmz
import xmo.wifi
import yaml
from . import xmo


def main():
    config = dict()
    if os.path.isfile('config.yaml'):
        with open('config.yaml') as f:
            config = yaml.safe_load(f)
    xmo.cli(default_map=config, _anyio_backend='asyncio')


if __name__ == '__main__':
    main()

