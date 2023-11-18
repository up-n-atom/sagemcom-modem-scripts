import asyncclick as click
from ipaddress import IPv4Address
from sagemcom_api.client import SagemcomClient
from . import xmo

@xmo.cli.command()
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

