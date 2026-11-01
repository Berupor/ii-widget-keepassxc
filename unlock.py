#!/usr/bin/env python3
import configparser
import csv
import os
import sys
from pathlib import Path

from gi.repository import Gio, GLib

BUS_NAME = "org.keepassxc.KeePassXC.MainWindow"
SECRETS = ("org.freedesktop.secrets", "/org/freedesktop/secrets", "org.freedesktop.Secret.Service")
COLLECTION = "org.freedesktop.Secret.Collection"
# openDatabase runs the KDF on KeePassXC's main thread before replying
TIMEOUT_MS = 60000
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
    return bus.call_sync(name, path, iface, method, args, None, Gio.DBusCallFlags.NONE, TIMEOUT_MS, None).unpack()


def keepassxc_running(bus):
    return call(bus, *DBUS, "NameHasOwner", GLib.Variant("(s)", (BUS_NAME,)))[0]


def owner(bus, name):
    return call(bus, *DBUS, "GetNameOwner", GLib.Variant("(s)", (name,)))[0]


def secrets_prop(bus, path, iface, prop):
    args = GLib.Variant("(ss)", (iface, prop))
    return call(bus, SECRETS[0], path, "org.freedesktop.DBus.Properties", "Get", args)[0]


# openDatabase replies the same whether the unlock worked, failed or was ignored
def locked_collections(bus):
    try:
        if owner(bus, SECRETS[0]) != owner(bus, BUS_NAME):
            return []
        paths = secrets_prop(bus, SECRETS[1], SECRETS[2], "Collections")
        return [secrets_prop(bus, p, COLLECTION, "Label") for p in paths if secrets_prop(bus, p, COLLECTION, "Locked")]
    except GLib.Error:
        return []


def main():
    databases = last_opened_databases()
    if sys.argv[1:] == ["--list"]:
        print("\n".join(databases))
        return 0
    password = sys.stdin.read()
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
    for label in locked_collections(bus):
        print(f"keepassxc_unlock_still_locked collection={label}", file=sys.stderr)
        failed = 1
    return failed


sys.exit(main())
