from aiohttp import ClientSession, ClientTimeout
from aiohttp.connector import TCPConnector
import asyncclick as click
from enum import Enum
from ipaddress import IPv4Address
import json
import os
import re
from sagemcom_api.client import SagemcomClient
from sagemcom_api.enums import EncryptionMethod
import yaml


class EnumChoice(click.Choice):
    def __init__(self, enum: Enum, case_sensitive=False):
        self.__enum = enum
        super().__init__(choices=[item.value for item in enum], case_sensitive=case_sensitive)

    def convert(self, value, param, ctx):
        if value is None or isinstance(value, Enum):
            return value
        converted_str = super().convert(value, param, ctx)
        return self.__enum(converted_str)


@click.group(chain=True)
@click.option('-H', '--host', default='192.168.2.1', help='Hostname or host IP')
@click.option('-u', '--username', default='admin', help='Administrator username')
@click.option('-p', '--password', required=True, help='Administrator password', prompt=True, hide_input=True)
@click.option('-a', '--authentication-method',
              default=EncryptionMethod.SHA512, type=EnumChoice(EncryptionMethod),
              help='Authentication method')
@click.pass_context
async def cli(ctx: click.Context, host: str, username: str, password: str, authentication_method: EncryptionMethod) -> None:
    ctx.obj = client = await ctx.with_async_resource(
        SagemcomClient(host, username, password, authentication_method,
            ClientSession(
                headers={"User-Agent": "XMO_REMOTE_CLIENT/1.0.0"},
                timeout=ClientTimeout(),
                connector=TCPConnector(ssl=True),
            ), True, keep_keys=True
        )
    )
    try:
        await client.login()
    except Exception as e:
        click.echo(e, err=True)
        raise click.Abort()


@cli.command()
@click.option('--path', required=True, multiple=True)
@click.pass_context
async def get_value(ctx: click.Context, path: str) -> None:
    client = ctx.find_object(SagemcomClient)
    if client is None:
        return
    for _path in path:
        try:
            value = await client.get_value_by_xpath(_path)
        except Exception as e:
            click.echo(e, err=True)
            raise click.Abort()
        else:
            click.echo(json.dumps(value, indent=2))


@cli.command()
@click.option('--path', required=True)
@click.option('--value', required=True)
@click.pass_context
async def set_value(ctx: click.Context, path: str, value: str) -> None:
    client = ctx.find_object(SagemcomClient)
    if client is None:
        return
    try:
        value = await client.set_value_by_xpath(path, value)
    except Exception as e:
        click.echo(e, err=True)
        raise click.Abort()


@cli.command()
@click.pass_context
async def get_wan_mode(ctx: click.Context) -> None:
    await ctx.invoke(get_value, path='Device/Services/BellNetworkCfg/WanMode')


@cli.command()
@click.pass_context
async def get_dns(ctx: click.Context) -> None:
    await ctx.invoke(get_value, path='Device/DNS')


@cli.command()
@click.option('-s', '--dns-servers', required=True, nargs=2, type=IPv4Address)
@click.pass_obj
async def set_dns_servers(client: SagemcomClient, dns_servers: tuple[IPv4Address]) -> None:
    try:
        forwards = await client.get_value_by_xpath('Device/DNS/Relay/Forwardings')
        autos = {forward['uid'] for forward in forwards \
            if forward.keys() >= {'uid', 'Alias', 'Interface', 'Enable'} and \
               forward['Alias'].startswith('IPCP') and \
               forward['Interface'].endswith('[IP_DATA]') and \
               forward['Enable']}
        statics = {forward['uid'] for forward in forwards \
            if forward.keys() >= {'uid', 'Alias', 'Interface'} and \
               forward['Alias'].startswith('STATIC') and \
               forward['Interface'].endswith(('[IP_DATA]', '[IP_BR_LAN]'))}
        for uid in autos:
            await client.set_value_by_xpath(f"Device/DNS/Relay/Forwardings/Forwarding[@uid={uid}]/Enable", False)
        for uid, dns_server in zip(statics, dns_servers):
            await client.set_value_by_xpath(f"Device/DNS/Relay/Forwardings/Forwarding[@uid={uid}]/DNSServer", dns_server)
            await client.set_value_by_xpath(
                 f"Device/DNS/Relay/Forwardings/Forwarding[@uid={uid}]/Interface",
                 'Device/IP/Interfaces/Interface[IP_BR_LAN]' if dns_server.is_private else 'Device/IP/Interfaces/Interface[IP_DATA]'
            )
            await client.set_value_by_xpath(f"Device/DNS/Relay/Forwardings/Forwarding[@uid={uid}]/Enable", True)
    except Exception as e:
        click.echo(e, err=True)
        raise click.Abort()


@cli.command()
@click.option('-r', '--radios', multiple=True)
@click.pass_obj
async def disable_wifi_radios(client: SagemcomClient, radios: tuple[str] | list[str]) -> None:
    try:
        value = await client.get_value_by_xpath('Device/WiFi/Radios')
        active_radios = {radio['Alias'] for radio in value if radio.keys() >= {'Alias', 'Enable'} and \
            radio['Enable']}
        if not len(radios):
            radios = click.prompt('Choose radio', type=click.Choice(active_radios), show_choices=True),
        invalid_radios = set(radios) - active_radios
        if len(invalid_radios):
            raise click.BadParameter("Invalid radio(s): {0}".format(", ".join(invalid_radios)))
        disable_radios = set(radios) & active_radios
        for alias in disable_radios:
            await client.set_value_by_xpath(f"Device/WiFi/Radios/Radio[Alias='{alias}']/Enable", False)
    except Exception as e:
        click.echo(e, err=True)
        raise click.Abort()


def validate_mac_address(ctx: click.Context, param: click.Parameter, value: str) -> str:
    result = value.upper()
    if not re.match(r"([0-9A-F]{2}:){5}[0-9A-F]{2}$", result):
        raise click.BadParameter('Invalid MAC address', ctx, param)
    return result


@cli.command()
@click.option('-m', '--mac-address', callback=validate_mac_address, prompt='MAC Address')
@click.pass_obj
async def enable_advanced_dmz(client: SagemcomClient, mac_address: str) -> None:
    try:
        await client.set_value_by_xpath('Device/Services/BellNetworkCfg/AdvancedDMZ/Enable', False)
        await client.set_value_by_xpath('Device/Services/BellNetworkCfg/AdvancedDMZ/AdvancedDMZhost', mac_address)
        await client.set_value_by_xpath('Device/Services/BellNetworkCfg/AdvancedDMZ/Enable', True)
    except Exception as e:
        click.echo(e, err=True)
        raise click.Abort()


if __name__ == '__main__':
    config = dict()
    if os.path.isfile('config.yaml'):
        with open('config.yaml') as f:
            config = yaml.safe_load(f)
    cli(default_map=config, _anyio_backend='asyncio')

