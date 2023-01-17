#!/usr/bin/python3

# https://stackoverflow.com/questions/49474199/appindicator3-change-icon
# https://askubuntu.com/questions/770036/appindicator3-set-indicator-icon-from-file-name-or-gdkpixbuf
# https://askubuntu.com/questions/751608/how-can-i-write-a-dynamically-updated-panel-app-indicator/756519#756519

import sys
import threading
import time
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
    state = lookup_state(info['battery_main_level'])
    charging = ""
    if (info['out_power'] < info['in_power']):
        charging = "-charging"
        
    indicator_widget.set_icon_full(f"battery-{state}{charging}{symbolic}", f"Battery at {info['battery_main_level']}%")
    indicator_widget.set_title(
        f"{info['out_power']}W total output"+
        f"\n{info['ac_out_power']}W AC output"+
        f"\n{info['dc_out_power']}W DC output"+
        f"\n{info['in_power']}W input"+
        (f"\n{info['battery_remain_discharge']*(100-info['battery_level_min'])/100} remaining" if info['out_power'] > info['in_power'] else "")
    )

requester = Requester(ecoflow_address, on_update)
main_terminated = threading.Event()

def connecter(main_terminated:threading.Event):
    while not main_terminated.is_set():
        if (requester.is_connected()):
            time.sleep(10.0)
        else:
            try:
                print("Connecting...")
                requester.connect()
            except gattlib.BTIOException as e:
                indicator_widget.set_icon_full(f"battery-missing{symbolic}", "")
                indicator_widget.set_title("No bluetooth connection")
                print(e)
                time.sleep(1.0)
                print("Retrying...")
threading.Thread(target=connecter, name="connecter", args=(main_terminated,), daemon=True).start()

Gtk.main()
main_terminated.set()
