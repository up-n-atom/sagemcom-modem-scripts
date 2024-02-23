import asyncclick as click
from sagemcom_api.client import SagemcomClient
from . import xmo


@xmo.cli.command()
@click.option('-r', '--radios', multiple=True)
@click.pass_obj
async def disable_wifi_radios(client: SagemcomClient, radios: tuple[str] | list[str]) -> None:
    try:
        _radios = await client.get_value_by_xpath('Device/WiFi/Radios')
        active_radios = {radio['alias'] for radio in _radios \
            if radio.keys() >= {'alias', 'enable'} and \
            radio['enable']}
        if not active_radios:
            click.echo('No active radios')
            return
        if not radios:
            radios = click.prompt('Choose radio', type=click.Choice(active_radios), show_choices=True),
        invalid_radios = set(radios) - active_radios
        if invalid_radios:
            raise click.BadParameter("Invalid radio(s): {0}".format(", ".join(invalid_radios)))
        disable_radios = set(radios) & active_radios
        for alias in disable_radios:
            await client.set_value_by_xpath(f"Device/WiFi/Radios/Radio[Alias='{alias}']/Enable", False)
    except Exception as e:
        ctx.fail(e)

