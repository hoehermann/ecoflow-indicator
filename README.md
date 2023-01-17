# ECOFLOW Indicator

This Python 3 application adds an indicator for your ECOFLOW battery to your notification area (hardware section). This is a proof of concept rather than a polished product.

Developed on Ubuntu 22.04 with XFCE and [systray](https://docs.xfce.org/xfce/xfce4-panel/systray).

Used with a DELTA 2. It uses Bluetooth LE GATT communication.

![screenshot](screenshot.png?raw=true "Screenshot of Application Indicator in Notification Area")

Invoke with your ECOFLOW's adress:

    python3 indicator.py AA:BB:CC:DD:EE:FF

Working directory must be the `indicator.py` location. I did not bother to use proper Python modules.

This contains parts of [nielsole's code](https://github.com/nielsole/ecoflow-bt-reverse-engineering) and [vwt12eh8's hassio-ecoflow](https://github.com/vwt12eh8/hassio-ecoflow). The latter decoded the protocol. I copied a modified variant of the code into this project since I failed to make it work with reactivex.
