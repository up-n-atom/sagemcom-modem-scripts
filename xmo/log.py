import time
from typing import Any

import asyncclick as click
import dpath
from sagemcom_api.client import SagemcomClient

from . import xmo


@xmo.cli.command()
@click.pass_context
async def flush_log(ctx: click.Context) -> None:
    try:
        async with xmo.flipflop('Device/DeviceInfo/FlushDeviceLog') as client:
            pass
    except Exception as e:
        ctx.fail(e)


@xmo.cli.command()
@click.pass_obj
async def read_log(client: SagemcomClient) -> None:
    async def api_request(action: dict, param: str) -> Any | None:
        response = await client._SagemcomClient__api_request_async([{'id': 0} | action], False)
        params = dpath.values(response, f"reply/actions/*/callbacks/*/parameters/{param}")
        return params[0] if params and len(params) == 1 else params
    try:
        method = 'getVendorLogDownloadURI'
        xpath = "Device/DeviceInfo/VendorLogFiles/VendorLogFile[@uid='1']"
        commands = await api_request({
            'method': 'getValue',
            'xpath': xpath,
            'options': {'capability-flags': {'interface': True}}
        }, 'capability/interfaces/*/commands/*/name')
        if method not in (commands if isinstance(commands, list) else [commands]):
            raise AttributeError('Command not supported by XMO client')
        uri = await api_request({'method': method, 'xpath': xpath}, 'uri')
        if not uri:
            raise ValueError('Failed to retrieve log URI')
        async with client.session.get(
            f"{client.protocol}://{client.host}{uri}?_={time.time_ns()}"
        ) as response:
            response.raise_for_status()
            async for line in response.content:
                click.echo(line.decode(), nl=False)
    except Exception as e:
        click.echo(e, err=True)
        raise click.Abort()
