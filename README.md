# Sagemcom Modem Remote Client

## Installation

Install [git](https://git-scm.com/downloads/) and [python3](https://www.python.org/downloads/)

```bash
git clone https://github.com/up-n-atom/sagemcom-modem-scripts.git
cd sagemcom-modem-scripts
git checkout cli
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

## Usage

```
Usage: xmo-remote-client.py [OPTIONS] COMMAND1 [ARGS]... [COMMAND2
                            [ARGS]...]...

Options:
  -H, --host TEXT                 Hostname or host IP
  -u, --username TEXT             Administrator username
  -p, --password TEXT             Administrator password  [required]
  -a, --authentication-method [MD5|SHA512]
                                  Authentication method
  --help                          Show this message and exit.

Commands:
  disable-wifi-radios
  enable-advanced-dmz
  get-dns
  get-value
  get-wan-mode
  set-dns-servers
  set-value
```

## Bell Home/Giga Hub Examples

> [!NOTE]
> The **Home Hub 4000** uses `MD5` authentication and can be enabled using the `-a` or `--authentication-method` switch, eg. `-a MD5`

```bash
source .venv/bin/activate
# List available commands
python3 xmo-remote-client.py --help
# Dump Device tree
python3 xmo-remote-client.py get-value --path "Device"
# Get WAN mode
python3 xmo-remote-client.py get-wan-mode
# Get DNS settings
python3 xmo-remote-client.py get-dns
# Enable local DNS server ie. Pi-hole
python3 xmo-remote-client.py set-dns-servers -s 192.168.2.254 192.168.2.254
# Disable 5G and 2.4G radios
python3 xmo-remote-client.py disable-wifi-radios -r RADIO5G -r RADIO2G4
# Disable radio w/ radio prompt
python3 xmo-remote-client.py disable-wifi-radios
# Enable advanced DMZ w/ MAC address prompt
python3 xmo-remote-client.py enable-advanced-dmz
# Disable advanced DMZ
python3 xmo-remote-client.py set-value --path "Device/Services/BellNetworkCfg/AdvancedDMZ/Enable" --value False
deactivate
```
