import asyncclick as click
import re
from sagemcom_api.client import SagemcomClient
from . import xmo


@xmo.cli.command()
@click.pass_context
async def get_onu_mode(ctx: click.Context) -> None:
    await ctx.invoke(xmo.get_value, path=['Device/Optical/G988/OnuMode'])


@xmo.cli.command()
@click.pass_context
async def get_wan_mode(ctx: click.Context) -> None:
    await ctx.invoke(xmo.get_value, path=['Device/Services/BellNetworkCfg/WanMode'])
