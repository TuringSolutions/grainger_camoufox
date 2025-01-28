virtualenv .pyenv
source .pyenv/bin/activate
pip3 install -U camoufox[geoip]
python3 -m camoufox fetch
sudo apt install -y libgtk-3-0 libx11-xcb1 libasound2
