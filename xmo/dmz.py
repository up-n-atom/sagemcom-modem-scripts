import re

import asyncclick as click

from . import xmo


def _validate_mac_address(ctx: click.Context, param: click.Parameter, value: str) -> str:
    result = value.upper()
    if not re.match(r"([0-9A-F]{2}:){5}[0-9A-F]{2}$", result):
        raise click.BadParameter('Invalid MAC address', ctx, param)
    return result


@xmo.cli.command()
@xmo.restrict(*xmo.BELL_MODELS)
@click.option('-m', '--mac-address', callback=_validate_mac_address, prompt='MAC Address')
@click.pass_context
async def enable_advanced_dmz(ctx: click.Context, mac_address: str) -> None:
    try:
        async with xmo.flipflop('Device/Services/BellNetworkCfg/AdvancedDMZ/Enable') as client:
            await client.set_value_by_xpath('Device/Services/BellNetworkCfg/AdvancedDMZ/AdvancedDMZhost', mac_address)
    except Exception as e:
        ctx.fail(e)


@xmo.cli.command()
@xmo.restrict(*xmo.BELL_MODELS)
@click.pass_context
async def disable_advanced_dmz(ctx: click.Context) -> None:
    await ctx.invoke(xmo.set_value, path='Device/Services/BellNetworkCfg/AdvancedDMZ/Enable', value=False)
