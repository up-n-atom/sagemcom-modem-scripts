import asyncclick as click
import re
from sagemcom_api.client import SagemcomClient
from . import xmo


def _validate_mac_address(ctx: click.Context, param: click.Parameter, value: str) -> str:
    result = value.upper()
    if not re.match(r"([0-9A-F]{2}:){5}[0-9A-F]{2}$", result):
        raise click.BadParameter('Invalid MAC address', ctx, param)
    return result


@xmo.cli.command()
@click.option('-m', '--mac-address', callback=_validate_mac_address, prompt='MAC Address')
@click.pass_obj
async def enable_advanced_dmz(client: SagemcomClient, mac_address: str) -> None:
    try:
        await client.set_value_by_xpath('Device/Services/BellNetworkCfg/AdvancedDMZ/Enable', False)
        await client.set_value_by_xpath('Device/Services/BellNetworkCfg/AdvancedDMZ/AdvancedDMZhost', mac_address)
        await client.set_value_by_xpath('Device/Services/BellNetworkCfg/AdvancedDMZ/Enable', True)
    except Exception as e:
        click.echo(e, err=True)
        raise click.Abort()


@xmo.cli.command()
@click.pass_context
async def disable_advanced_dmz(ctx: click.Context) -> None:
    await ctx.invoke(xmo.set_value, path='Device/Services/BellNetworkCfg/AdvancedDMZ/Enable', value=False)

