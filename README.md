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
pip install dist/xmo_remote_client-0.0.10-py3-none-any.whl
deactivate
```

## Install via Github release

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install https://github.com/up-n-atom/sagemcom-modem-scripts/releases/download/v0.0.10/xmo_remote_client-0.0.10-py3-none-any.whl
deactivate
```

## Use from Source

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
python3 -m xmo ...
```

## Usage

```
Usage: python -m xmo [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

Options:
  -H, --host IPV4ADDRESS          Hostname or host IP
  -u, --username TEXT             Administrator username
  -p, --password TEXT             Administrator password
  -a, --auth-method [MD5|MD5_NONCE|SHA512]
                                  Authentication method
  --version                       Show the version and exit.
  --help                          Show this message and exit.

Commands:
  disable-advanced-dmz
  disable-wifi-radios
  enable-advanced-dmz
  flush-log
  get-onu-mode
  get-value
  get-wan-mode
  read-log
  set-dns-servers
  set-value


Usage: python -m xmo get-value [OPTIONS]

Options:
  --path TEXT                    [required]
  --format [json|yaml|toml|xml]  Output format  [default: json]
  --help                         Show this message and exit.


Usage: python -m xmo disable-wifi-radios [OPTIONS]

Options:
  -r, --radios TEXT
  --help             Show this message and exit.


Usage: python -m xmo set-dns-servers [OPTIONS]

Options:
  -s, --dns-servers IPV4ADDRESS...
                                  [required]
  --help                          Show this message and exit.


Usage: python -m xmo set-value [OPTIONS]

Options:
  --path TEXT   [required]
  --value TEXT  [required]
  --help        Show this message and exit.

```

### Example Usage

> [!NOTE]
> The **Home Hub 4000** uses `MD5` authentication, which can be enabled using either `-a` _or_ `--auth-method` option, eg. `-a MD5`

```bash
# List available commands
xmo-remote-client --help
# Dump Device tree as json
xmo-remote-client get-value --path "Device"
# Dump Device tree as yaml
xmo-remote-client get-value --path "Device" --format yaml
# Dump Device tree as toml
xmo-remote-client get-value --path "Device" --format toml
# Dump Device tree as paths only with the help of jq
xmo-remote-client get-value --path "Device" | jq -r 'def uid: (select(type == "number") | "[@uid=\(.)]") // .; paths | map(uid) | join("\/")'
# Get WAN mode
xmo-remote-client get-wan-mode
# Enable local DNS server ie. Pi-hole
xmo-remote-client set-dns-servers -s 192.168.2.254 192.168.2.254
# Disable 5G and 2.4G radios
xmo-remote-client disable-wifi-radios -r RADIO5G -r RADIO2G4
# Disable all radios
xmo-remote-client disable-wifi-radios --radios all
# Disable radio w/ radio prompt
xmo-remote-client disable-wifi-radios
# Enable advanced DMZ w/ MAC address prompt
xmo-remote-client enable-advanced-dmz
# Get ONU mode
xmo-remote-client get-onu-mode
# Get multiple values ie. OLT info
xmo-remote-client get-value --path "Device/Optical/G988/General/OltG/OltVendorId" --path "Device/Optical/G988/General/OltG/Version"
# Read system log
xmo-remote-client read-log
# Flush system log
xmo-remote-client flush-log

```
