# Sagemcom Modem Remote Client

## Build Package
```bash
git clone https://github.com/up-n-atom/sagemcom-modem-scripts.git
cd sagemcom-modem-scripts
git checkout cli
python3 -m build
```

## Installation

Install [git](https://git-scm.com/downloads/) and [python3](https://www.python.org/downloads/)

## Install via build package

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install dist/xmo_remote_client-0.0.1-py3-none-any.whl
deactivate
```

## Install via Github release

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install https://github.com/up-n-atom/sagemcom-modem-scripts/releases/download/v0.0.1/xmo_remote_client-0.0.1-py3-none-any.whl
deactivate
```

## Usage

```
Usage: xmo-remote-client [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

Options:
  -H, --host IPV4ADDRESS          Hostname or host IP
  -u, --username TEXT             Administrator username
  -p, --password TEXT             Administrator password  [required]
  -a, --auth-method [MD5|SHA512]  Authentication method
  --help                          Show this message and exit.

Commands:
  disable-advanced-dmz
  disable-wifi-radios
  enable-advanced-dmz
  get-value
  set-dns-servers
  set-value
```

### Bell Home/Giga Hub Examples

> [!NOTE]
> The **Home Hub 4000** uses `MD5` authentication, which can be enabled using either `-a` _or_ `--auth-method` option, eg. `-a MD5`

```bash
cd sagemcom-modem-scripts
source .venv/bin/activate
# List available commands
python3 xmo-remote-client.py --help
# Dump Device tree
python3 xmo-remote-client.py get-value --path "Device"
# Get WAN mode
python3 xmo-remote-client.py get-value --path "Device/Services/BellNetworkCfg/WanMode"
# Enable local DNS server ie. Pi-hole
python3 xmo-remote-client.py set-dns-servers -s 192.168.2.254 192.168.2.254
# Disable 5G and 2.4G radios
python3 xmo-remote-client.py disable-wifi-radios -r RADIO5G -r RADIO2G4
# Disable radio w/ radio prompt
python3 xmo-remote-client.py disable-wifi-radios
# Enable advanced DMZ w/ MAC address prompt
python3 xmo-remote-client.py enable-advanced-dmz
# Get multiple values ie. OLT info
python3 xmo-remote-client.py get-value --path "Device/Optical/G988/General/OltG/OltVendorId" --path "Device/Optical/G988/General/OltG/Version"
deactivate
```
