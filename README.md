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

## Bell Home Hub 4000 Examples

```bash
source .venv/bin/activate
# List available commands
python3 xmo-remote-client.py --help
# Dump Device tree
python3 xmo-remote-client.py -a MD5 get-value --path "Device"
# Get WAN mode
python3 xmo-remote-client.py -a MD5 get-wan-mode
# Get DNS settings
python3 xmo-remote-client.py -a MD5 get-dns
# Enable local DNS server ie. Pi-hole
python3 xmo-remote-client.py -a MD5 set-dns-servers -s 192.168.2.254 192.168.2.254
# Disable 5G and 2.4G radios
python3 xmo-remote-client.py -a MD5 disable-wifi-radios -r RADIO5G -r RADIO2G4
```
