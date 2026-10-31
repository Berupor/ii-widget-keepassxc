#!/usr/bin/env python3
import configparser
import csv
import os
import sys
from pathlib import Path

from gi.repository import Gio, GLib

BUS_NAME = "org.keepassxc.KeePassXC.MainWindow"
DBUS = ("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus")


def last_opened_databases():
    state_home = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    ini = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        ini.read(state_home / "keepassxc/keepassxc.ini")
    except configparser.Error:
        return []
    raw = ini.get("General", "LastOpenedDatabases", fallback="")
    # QSettings list: comma separated, entries holding a comma come quoted
    entries = next(csv.reader([raw], skipinitialspace=True), [])
    return [e for e in entries if e.startswith("/")]


def call(bus, name, path, iface, method, args):
    return bus.call_sync(name, path, iface, method, args, None, Gio.DBusCallFlags.NONE, 5000, None).unpack()


def keepassxc_running(bus):
    return call(bus, *DBUS, "NameHasOwner", GLib.Variant("(s)", (BUS_NAME,)))[0]


def main():
    password = sys.stdin.read()
    databases = last_opened_databases()
    if not password or not databases:
        return 1
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    if not keepassxc_running(bus):
        return 1
    failed = 0
    for db in databases:
        try:
            call(bus, BUS_NAME, "/keepassxc", BUS_NAME, "openDatabase", GLib.Variant("(ss)", (db, password)))
        except GLib.Error as e:
            print(f"keepassxc_unlock_failed db={db} error={e.message}", file=sys.stderr)
            failed = 1
    return failed


sys.exit(main())
