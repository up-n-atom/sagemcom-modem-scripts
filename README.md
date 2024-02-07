# Sagemcom Modem Remote Client

## Prerequisite 

Install [git](https://git-scm.com/downloads/) and [python3](https://www.python.org/downloads/)

## Build Package
```bash
git clone https://github.com/up-n-atom/sagemcom-modem-scripts.git
cd sagemcom-modem-scripts
git checkout cli
pip3 install build
python3 -m build
```

## Install via build package

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install dist/xmo_remote_client-0.0.4-py3-none-any.whl
deactivate
```

## Install via Github release

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install https://github.com/up-n-atom/sagemcom-modem-scripts/releases/download/v0.0.4/xmo_remote_client-0.0.4-py3-none-any.whl
deactivate
```

## Usage

```
Usage: python -m xmo [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

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
  get-onu-mode
  get-value
  get-wan-mode
  set-dns-servers
  set-value
```

### Bell Home/Giga Hub Examples

> [!NOTE]
> The **Home Hub 4000** uses `MD5` authentication, which can be enabled using either `-a` _or_ `--auth-method` option, eg. `-a MD5`

```bash
source .venv/bin/activate
# List available commands
xmo-remote-client --help
# Dump Device tree
xmo-remote-client get-value --path "Device"
# Get WAN mode
xmo-remote-client get-wan-mode
# Enable local DNS server ie. Pi-hole
xmo-remote-client set-dns-servers -s 192.168.2.254 192.168.2.254
# Disable 5G and 2.4G radios
xmo-remote-client disable-wifi-radios -r RADIO5G -r RADIO2G4
# Disable radio w/ radio prompt
xmo-remote-client disable-wifi-radios
# Enable advanced DMZ w/ MAC address prompt
xmo-remote-client enable-advanced-dmz
# Get ONU mode
xmo-remote-client get-onu-mode
# Get multiple values ie. OLT info
xmo-remote-client get-value --path "Device/Optical/G988/General/OltG/OltVendorId" --path "Device/Optical/G988/General/OltG/Version"
deactivate
```
