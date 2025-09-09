import time

import asyncclick as click
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
    try:
        # uncertain if this api is supported globally so access sagemcom_api client private methods improperly
        actions = {
            "id": 0,
            "method": "getVendorLogDownloadURI",
            "xpath": "Device/DeviceInfo/VendorLogFiles/VendorLogFile",
            "parameters": {
                "FileName": "utilsLogFile",
            },
            "event-id": "1",
        }
        response = await client._SagemcomClient__api_request_async([actions], False)
        data = client._SagemcomClient__get_response(response)
        api_host = f"{client.protocol}://{client.host}/{data['uri']}?_={time.time_ns()}"
        async with client.session.get(api_host) as response:
            async for line in response.content:
                click.echo(line, nl=False)
    except Exception as e:
        click.echo(e, err=True)
        raise click.Abort()