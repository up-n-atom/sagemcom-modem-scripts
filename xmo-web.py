import asyncclick as click
from enum import Enum
from ipaddress import IPv4Address
from json import dumps
from sagemcom_api.client import SagemcomClient
from sagemcom_api.enums import EncryptionMethod


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
@click.option('-p', '--password', required=True, help='Administrator password')
@click.option('-a', '--authentication-method',
              default=EncryptionMethod.SHA512, type=EnumChoice(EncryptionMethod),
              help='Authentication method')
@click.pass_context
async def cli(ctx: click.Context, host: str, username: str, password: str, authentication_method: EncryptionMethod) -> None:
    ctx.obj = client = await ctx.with_async_resource(
        SagemcomClient(host, username, password, authentication_method, ssl=True, keep_keys=True)
    )
    try:
        await client.login()
    except Exception as e:
        raise click.Abort(e)


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
    else:
        click.echo(dumps(value, indent=2))


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


@cli.command()
@click.pass_context
async def get_wan_mode(ctx: click.Context) -> None:
    await ctx.invoke(get_value, path='Device/Services/BellNetworkCfg/WanMode')


if __name__ == '__main__':
    cli(_anyio_backend='asyncio')

