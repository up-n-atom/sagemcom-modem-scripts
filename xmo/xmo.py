import asyncclick as click
import json
from aiohttp import ClientSession, ClientTimeout
from aiohttp.connector import TCPConnector
from contextlib import asynccontextmanager
from enum import Enum
from ipaddress import IPv4Address
from sagemcom_api.client import SagemcomClient
from sagemcom_api.enums import EncryptionMethod
from . import __version__


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
@click.option('-H', '--host', default='192.168.2.1', help='Hostname or host IP', type=IPv4Address)
@click.option('-u', '--username', default='admin', help='Administrator username')
@click.option('-p', '--password', required=True, help='Administrator password', prompt=True, hide_input=True)
@click.option('-a', '--auth-method',
              default=EncryptionMethod.SHA512, type=EnumChoice(EncryptionMethod),
              help='Authentication method')
@click.version_option(__version__)
@click.pass_context
async def cli(ctx: click.Context, host: IPv4Address, username: str, password: str, auth_method: EncryptionMethod) -> None:
    ctx.obj = client = await ctx.with_async_resource(
        SagemcomClient(host, username, password, auth_method,
            ClientSession(
                headers={"User-Agent": "XMO_REMOTE_CLIENT/1.0.0"},
                timeout=ClientTimeout(),
                connector=TCPConnector(ssl=True),
            ), True
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
async def get_value(ctx: click.Context, path: list[str]) -> None:
    if (client := ctx.find_object(SagemcomClient)) is None:
        return
    for _path in path:
        try:
            value = await client.get_value_by_xpath(_path)
        except Exception as e:
            click.echo(e, err=True)
            continue
        else:
            click.echo(json.dumps(value, indent=2))


@cli.command()
@click.option('--path', required=True)
@click.option('--value', required=True)
@click.pass_context
async def set_value(ctx: click.Context, path: str, value: str) -> None:
    if (client := ctx.find_object(SagemcomClient)) is None:
        return
    try:
        value = await client.set_value_by_xpath(path, value)
    except Exception as e:
        click.echo(e, err=True)
        raise click.Abort()


@asynccontextmanager
async def flipflop(xpath: str) -> None:
    if (client := click.get_current_context().find_object(SagemcomClient)) is None:
        raise ValueError('client not found')
    await client.set_value_by_xpath(xpath, False)
    try:
        yield client
    finally:
        await client.set_value_by_xpath(xpath, True)

