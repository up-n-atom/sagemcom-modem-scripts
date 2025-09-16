from contextlib import asynccontextmanager
from enum import Enum, StrEnum
from ipaddress import IPv4Address
import json
from typing import Any, Awaitable, Callable

import asyncclick as click
from aiohttp import ClientSession, ClientTimeout
from aiohttp.connector import TCPConnector
from sagemcom_api.client import SagemcomClient
from sagemcom_api.enums import EncryptionMethod

from . import __version__


def __patch_get_response_value(self, response: Any, index: int = 0) -> Any:
    try:
        value = self._SagemcomClient__get_response(response, index)["value"]
    except (KeyError, IndexError):
        value = None
    return value

try:
    # monkey-patch out decamelize as it breaks path discovery
    SagemcomClient._SagemcomClient__get_response_value = __patch_get_response_value
    # remove methods that rely on decamelize and/or serve no purpose ie. decoupling client from "Device"
    del SagemcomClient.get_device_info
    del SagemcomClient.get_hosts
    del SagemcomClient.get_port_mappings
except AttributeError:
    exit('Failed to patch SagemcomClient API')


class EnumChoice(click.Choice):
    def __init__(self, enum: Enum, case_sensitive: bool = False) -> None:
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
@click.password_option('-p', '--password', help='Administrator password')
@click.option('-a', '--auth-method',
              default=EncryptionMethod.SHA512, type=EnumChoice(EncryptionMethod),
              help='Authentication method')
@click.version_option(__version__)
@click.pass_context
async def cli(ctx: click.Context, host: IPv4Address, username: str, password: str, auth_method: EncryptionMethod) -> None:
    ctx.obj = client = await ctx.with_async_resource(
        XmoClient(host, username, password, auth_method,
            ClientSession(
                headers={"User-Agent": "XMO_REMOTE_CLIENT/1.0.0"},
                timeout=ClientTimeout(),
                connector=TCPConnector(ssl=False),
            ), True
        )
    )
    try:
        await client.login()
    except Exception as e:
        ctx.fail(e)


@cli.command()
@click.option('--path', required=True, multiple=True)
@click.pass_context
async def get_value(ctx: click.Context, path: list[str]) -> None:
    client = ctx.find_object(SagemcomClient)
    if client is None:
        ctx.fail('Client not found')
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
    client = ctx.find_object(SagemcomClient)
    if client is None:
        ctx.fail('Client not found')
    try:
        value = await client.set_value_by_xpath(path, value)
    except Exception as e:
        ctx.fail(e)


@asynccontextmanager
async def flipflop(xpath: str, value: bool | None = False) -> None:
    def to_bool(value) -> bool:
        return isinstance(value, str) and value.lower() in ('true', 'on', '1')
    client = click.get_current_context().find_object(SagemcomClient)
    if client is None:
        raise ValueError('Client not found')
    if value is None:
        value = not to_bool(await client.get_value_by_xpat(xpath))
    await client.set_value_by_xpath(xpath, value)
    try:
        yield client
    finally:
        await client.set_value_by_xpath(xpath, not value)


class Model(StrEnum):
    FAST5250 = '5250'
    FAST5566 = '5566'
    FAST5689 = '5689'
    FAST5690 = '5690'
    FAST5697 = '5697'

BELL_MODELS = frozenset({Model.FAST5250, Model.FAST5566, Model.FAST5689, Model.FAST5690, Model.FAST5697})


AsyncCallable = Callable[..., Awaitable[None]]


def restrict(*models: Model | str) -> Callable[[AsyncCallable], AsyncCallable]:
    if not models:
        raise ValueError('restrict() requires at least one model')
    models = frozenset(Model(model) for model in models)
    def decorator(func: AsyncCallable) -> AsyncCallable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> None:
            try:
                client = click.get_current_context().find_object(SagemcomClient)
                if client is None:
                    raise ValueError('Client not found')
                model = await client.get_value_by_xpath('Device/DeviceInfo/ModelName')
                if model not in models:
                    raise RuntimeError(f"Command not supported by model {model}")
            except Exception as e:
                click.echo(e, err=True)
                raise click.Abort()
            return await func(*args, **kwargs)
        return wrapper
    return decorator