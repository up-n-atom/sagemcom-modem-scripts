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
from typing import Any
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
@click.option('-p', '--password', required=True, help='Administrator password', prompt=True)
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
@click.option('--path', required=True)
@click.pass_context
async def get_value(ctx: click.Context, path: str) -> None:
    if not isinstance(ctx.obj, SagemcomClient):
        return
    try:
        value = await ctx.obj.get_value_by_xpath(path)
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
    if not isinstance(ctx.obj, SagemcomClient):
        return
    try:
        value = await ctx.obj.set_value_by_xpath(path, value)
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


def validate_dns_servers(ctx: click.Context, param: str, value: Any) -> tuple[IPv4Address]:
    if isinstance(value, tuple):
        return value
    elif isinstance(value, list):
        value = " ".join(value)
    dns_servers = set()
    for dns_server in value.split(' ', maxsplit=1):
        try:
            dns_servers.add(IPv4Address(dns_server))
        except:
            raise click.BadParameter(f"Invalid IPv4 address: {dns_server}")
    return tuple(dns_servers)


@cli.command()
@click.option('--dns-servers', type=click.UNPROCESSED, callback=validate_dns_servers, prompt='DNS servers seperated by a space')
@click.pass_obj
async def set_dns_servers(client: SagemcomClient, dns_servers: tuple[IPv4Address]) -> None:
    try:
        forwards = await client.get_value_by_xpath('Device/DNS/Relay/Forwardings')
        autos = {forward['uid'] for forward in forwards \
            if 'uid' in forward and \
               'Alias' in forward and forward['Alias'].startswith('IPCP') and \
               'Interface' in forward and forward['Interface'].endswith('[IP_DATA]') and \
               'Enable' in forward and forward['Enable']}
        statics = {forward['uid'] for forward in forwards \
            if 'uid' in forward and \
               'Alias' in forward and forward['Alias'].startswith('STATIC') and \
               'Interface' in forward and forward['Interface'].endswith(('[IP_DATA]', '[IP_BR_LAN]'))}
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
@click.option('-r', '--radio', multiple=True)
@click.pass_obj
async def disable_wifi_radio(client: SagemcomClient, radio: tuple | list) -> None:
    try:
        value = await client.get_value_by_xpath('Device/WiFi/Radios')
        active_radios = {radio['Alias'] for radio in value if 'Alias' in radio and \
            'Enable' in radio and radio['Enable']}
        if radio is None or not len(radio):
            radio = click.prompt('Choose radio', type=click.Choice(active_radios), show_choices=True),
        radios = set(radio) - active_radios
        if len(radios):
            raise click.BadParameter("Invalid radio(s): {0}".format(", ".join(radios)))
        radios = set(radio) & active_radios
        for alias in radios:
            await client.set_value_by_xpath(f"Device/WiFi/Radios/Radio[Alias='{alias}']/Enable", False)
    except Exception as e:
        click.echo(e, err=True)
        raise click.Abort()


def validate_mac_address(ctx: click.Context, param: str, value: str) -> str:
    if not re.match(r"([0-9A-F]{2}:){5}[0-9A-F]{2}$", value):
        raise click.BadParameter("Invalid MAC address", param=value)
    return value


@cli.command()
@click.option('-m', '--mac-address', type=click.UNPROCESSED, callback=validate_mac_address, prompt=True)
@click.pass_obj
async def enable_advanced_dmz(client: SagemcomClient, mac_address: str) -> None:
    await client.set_value_by_xpath('Device/Services/BellNetworkCfg/AdvancedDMZ/Enable', False)
    await client.set_value_by_xpath('Device/Services/BellNetworkCfg/AdvancedDMZ/AdvancedDMZhost', mac_address)
    await client.set_value_by_xpath('Device/Services/BellNetworkCfg/AdvancedDMZ/Enable', True)


if __name__ == '__main__':
    config = dict()
    if os.path.isfile('config.yaml'):
        with open('config.yaml') as f:
            config = yaml.safe_load(f)
    cli(default_map=config, _anyio_backend='asyncio')

