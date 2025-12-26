from collections.abc import Awaitable, Callable, Iterable, Mapping
from contextlib import asynccontextmanager
from enum import Enum, StrEnum
from functools import wraps
from ipaddress import IPv4Address
import json
import sys
from typing import Any
import urllib
from xml.dom.minidom import parseString

import asyncclick as click
from aiohttp import ClientSession, ClientTimeout
from aiohttp.connector import TCPConnector
import backoff
from dicttoxml import dicttoxml
import dpath
from sagemcom_api.client import SagemcomClient, retry_login
from sagemcom_api.enums import EncryptionMethod
from sagemcom_api.exceptions import AuthenticationException, LoginRetryErrorException, LoginTimeoutException, InvalidSessionException
import toml
import yaml

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
    sys.exit('Failed to patch SagemcomClient API')


class XmoClient(SagemcomClient):

    # Could monkey-patch SagemcomClient.__get_response_value here, maybe later...

    # Fix quoting xpaths - it's missing '@' as a safe char within SagemcomClient.get_value_by_xpath, and
    # quoting is totally broken within SagemcomClient.get_values_by_xpaths. Also, Dont Repeat Yourself!!
    @backoff.on_exception(
        backoff.expo,
        (
            AuthenticationException,
            LoginRetryErrorException,
            LoginTimeoutException,
            InvalidSessionException,
        ),
        max_tries=1,
        on_backoff=retry_login,
    )
    async def get_values_by_xpaths(self, xpaths: Iterable[str] | Mapping[str, str], options: dict | None = None) -> dict:
        actions = [
            {
                'id': i,
                'method': 'getValue',
                'xpath': urllib.parse.quote(xpath, "/=[]'@"),
                'options': options if options else {},
            }
            for i, xpath in enumerate(xpaths.values() if isinstance(xpaths, dict) else xpaths)
        ]
        response = await self._SagemcomClient__api_request_async(actions, False)
        values = dpath.values(response, 'reply/actions/*/callbacks/*/parameters/value')
        return dict(zip(xpaths.keys() if isinstance(xpaths, dict) else xpaths, values))

    async def get_value_by_xpath(self, xpath: str, options: dict | None = None) -> Any:
        return (await self.get_values_by_xpaths([xpath], options))[xpath]

    async def set_value_by_xpath(self, xpath: str, value: str, options: dict | None = None) -> dict:
        actions = {
            'id': 0,
            'method': 'setValue',
            'xpath': urllib.parse.quote(xpath, "/=[]'@"),
            'parameters': {'value': str(value)},
            'options': options if options else {},
        }

        response = await self._SagemcomClient__api_request_async([actions], False)

        return response


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
@click.option('--format', 'fmt',
    default='json', type=click.Choice(['json', 'yaml', 'toml', 'xml'], case_sensitive=False), show_default=True,
    help="Output format")
@click.pass_context
async def get_value(ctx: click.Context, path: list[str], fmt: str) -> None:
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
            if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
                match fmt:
                    case 'yaml':
                        click.echo(yaml.safe_dump(value))
                    case 'toml':
                        click.echo(toml.dumps(value))
                    case 'xml':
                        click.echo(parseString(
                            dicttoxml(value, xml_declaration=False, attr_type=False, return_bytes=False)
                        ).toprettyxml())
                    case _:
                        click.echo(json.dumps(value, indent=2))
            else:
                click.echo(value)


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
        value = not to_bool(await client.get_value_by_xpath(xpath))
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
