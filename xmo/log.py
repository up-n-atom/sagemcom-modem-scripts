import asyncclick as click
import re
from sagemcom_api.client import SagemcomClient
from . import xmo


@xmo.cli.command()
async def flush_log() -> None:
    try:
        async with xmo.flipflop('Device/DeviceInfo/FlushDeviceLog') as client:
            pass
    except Exception as e:
        click.echo(e, err=True)
        raise click.Abort()
