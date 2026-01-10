import asyncclick as click
from sagemcom_api.client import SagemcomClient

from . import xmo


async def _toggle_wifi_radios(client: SagemcomClient, radios: tuple[str] | list[str], status: bool) -> None:
    try:
        _radios = await client.get_value_by_xpath('Device/WiFi/Radios')
        _radios = {radio['Alias'] for radio in _radios \
            if radio.keys() >= {'Alias', 'Enable'} and \
            radio['Enable'] == status}
        if not _radios:
            await click.echo('No active radios' if status else 'No inactive radios')
            return
        if not radios:
            radios = await click.prompt('Choose radio', type=click.Choice(list(_radios) + ['all']), show_choices=True),
        if 'all' not in radios:
            if invalid_radios := set(radios) - _radios:
                raise click.BadParameter("Invalid radio(s): {0}".format(", ".join(invalid_radios)))
            _radios = set(radios) & _radios
        for alias in _radios:
            await client.set_value_by_xpath(f"Device/WiFi/Radios/Radio[Alias='{alias}']/Enable", not status)
    except Exception as e:
        client.echo(e, err=True)
        raise click.Abort()
    
    
async def _set_wifi_radio_parameter(client: SagemcomClient, radios: tuple[str] | list[str], parameter: str, value) -> None:
    try:
        _radios = await client.get_value_by_xpath('Device/WiFi/Radios')
        _radios = {radio['Alias'] for radio in _radios if radio.keys() >= {'Alias', parameter}}
        if not _radios:
            await click.echo('No radios found')
            return
        if not radios:
            radios = await click.prompt('Choose radio', type=click.Choice(list(_radios) + ['all']), show_choices=True),
        if 'all' not in radios:
            if invalid_radios := set(radios) - _radios:
                raise click.BadParameter("Invalid radio(s): {0}".format(", ".join(invalid_radios)))
            _radios = set(radios) & _radios
        for alias in _radios:
            await client.set_value_by_xpath(f"Device/WiFi/Radios/Radio[Alias='{alias}']/{parameter}", value)
    except Exception as e:
        client.echo(e, err=True)
        raise click.Abort()


@xmo.cli.command()
@click.option('-r', '--radios', multiple=True)
@click.pass_obj
async def disable_wifi_radios(client: SagemcomClient, radios: tuple[str] | list[str]) -> None:
    await _toggle_wifi_radios(client, radios, True)


@xmo.cli.command()
@click.option('-r', '--radios', multiple=True)
@click.pass_obj
async def enable_wifi_radios(client: SagemcomClient, radios: tuple[str] | list[str]) -> None:
    await _toggle_wifi_radios(client, radios, False)

@xmo.cli.command()
@click.option('-r', '--radios', multiple=True)
@click.option('-a', '--attribute', required=True)
@click.option('-v', '--value', required=True)
@click.pass_obj
async def set_wifi_radio_parameter(client: SagemcomClient, radios: tuple[str] | list[str], attribute: str, value) -> None:
    await _set_wifi_radio_parameter(client, radios, attribute, value)