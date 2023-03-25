#!/usr/bin/python3

# https://stackoverflow.com/questions/49474199/appindicator3-change-icon
# https://askubuntu.com/questions/770036/appindicator3-set-indicator-icon-from-file-name-or-gdkpixbuf
# https://askubuntu.com/questions/751608/how-can-i-write-a-dynamically-updated-panel-app-indicator/756519#756519

import sys
import threading
import time
import datetime
import gattlib
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("AppIndicator3", "0.1") # gir1.2-appindicator3-0.1
from gi.repository import Gtk, AppIndicator3
from gi.repository import Notify
from ecoflow_gatt import Requester

def _quit(self):
    Gtk.main_quit()

def _menu():
    menu = Gtk.Menu()
    item_quit = Gtk.MenuItem(label='Quit')
    item_quit.connect('activate', _quit)
    menu.append(item_quit)
    #menu.append(Gtk.SeparatorMenuItem())
    menu.show_all()
    return menu
    
INDICATOR_ID = "ecoflow_indicator"

symbolic = "-symbolic"

indicator_widget = AppIndicator3.Indicator.new(
    INDICATOR_ID,
    f"battery-missing{symbolic}",
    AppIndicator3.IndicatorCategory.HARDWARE
)
indicator_widget.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
indicator_widget.set_menu(_menu())
indicator_widget.set_title("No bluetooth connection")
Notify.init(INDICATOR_ID)

state_mapping = [(90, "full"),
(50, "good"),
(30, "low"),
(25, "caution"),
(0, "empty")]
def lookup_state(level: int):
    for threshold, state in state_mapping:
        if level >= threshold:
            return state

ecoflow_address = sys.argv[1]
def on_update(info):
    import pprint
    pprint.pprint(info)
    state = lookup_state(info['battery_main_level'])
    
    # info['out_power'] < info['in_power'] these are unreliable
    charging = isinstance(info['battery_remain_charge'], datetime.timedelta)
    discharging = isinstance(info['battery_remain_discharge'], datetime.timedelta)
    if (charging and discharging):
        discharging = info['battery_remain_discharge'] < info['battery_remain_charge']
        charging = info['battery_remain_charge'] < info['battery_remain_discharge']
    if (charging):
        charging = "-charging"
    else:
        charging = ""
        
    indicator_widget.set_icon_full(f"battery-{state}{charging}{symbolic}", f"Battery at {info['battery_main_level']}%")
    description = [
        #f"{info['battery_out_power']}W battery output", # always zero
        #f"{info['battery_in_power']}W battery input", # always zero
        #f"{info['out_power']}W total output", # updates only sometimes
        f"{info['ac_out_power']}W AC output",
        f"{info['typec_out1_power']+info['typec_out2_power']}W USB-C output",
        f"{info['usb_out1_power']+info['usb_out2_power']+info['usbqc_out1_power']+info['usbqc_out2_power']}W USB-A output",
        f"{info['in_power']}W input",
        f"{info['battery_cycles']} cycles",
        f"{info['battery_capacity_remain']} mAh ({int(100*info['battery_capacity_remain']/(info['battery_capacity_design']+1))}%) stored",
        ]
    if (discharging):
        description.append(f"{info['battery_remain_discharge']*(100-info['battery_level_min'])/100} remaining until {info['battery_level_min']}%")
    if (charging):
        description.append(f"{info['battery_remain_charge']} remaining until 100 %")
    indicator_widget.set_title('\n'.join(description))

main_terminated = threading.Event()

def connecter(main_terminated:threading.Event):
    requester = None
    while (not main_terminated.is_set() and (requester is None or not requester.is_connected())):
        try:
            requester = Requester(ecoflow_address, on_update)
            if (not requester.is_connected()):
                print("Connecting...")
                requester.connect()
                print("Connected.")
        except gattlib.BTIOException as e:
            indicator_widget.set_icon_full(f"battery-missing{symbolic}", "No bluetooth connection")
            indicator_widget.set_title(str(e))
            time.sleep(1.0)
            print("Retrying...")
threading.Thread(target=connecter, name="connecter", args=(main_terminated,), daemon=True).start()

Gtk.main()
main_terminated.set()
