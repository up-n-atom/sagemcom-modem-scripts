import asyncclick as click
from enum import Enum
from ipaddress import IPv4Address
import json
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


@cli.command()
@click.pass_context
async def get_wan_mode(ctx: click.Context) -> None:
    await ctx.invoke(get_value, path='Device/Services/BellNetworkCfg/WanMode')


@cli.command()
@click.pass_context
async def get_dns(ctx: click.Context) -> None:
    await ctx.invoke(get_value, path='Device/DNS')


def validate_dns_servers(ctx, param, value) -> tuple[IPv4Address]:
    if isinstance(value, tuple):
        return value
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
    for i, dns_server in enumerate(dns_servers, start=1):
        try:
            await client.set_value_by_xpath(f"Device/DNS/Relay/Forwardings/Forwarding[@uid={i}]/DNSServer", dns_server)
            await client.set_value_by_xpath(
                f"Device/DNS/Relay/Forwardings/Forwarding[@uid={i}]/Interface",
                'Device/IP/Interfaces/Interface[IP_BR_LAN]' if dns_server.is_private else 'Device/IP/Interfaces/Interface[IP_DATA]'
            )
        except Exception as e:
            click.echo(e, err=True)
            break
    else:
        try:
            await client.set_value_by_xpath('Device/DNS/Client/Servers/Server[@uid=1]/Enable', True)
        except Exception as e:
            click.echo(e, err=True)


if __name__ == '__main__':
    cli(_anyio_backend='asyncio')

