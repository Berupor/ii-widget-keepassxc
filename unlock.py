#!/usr/bin/env python3
import os
import string
import sys
from pathlib import Path

from gi.repository import Gio, GLib

BUS_NAME = "org.keepassxc.KeePassXC.MainWindow"
APP_ID = "org.keepassxc.KeePassXC"
SECRETS = ("org.freedesktop.secrets", "/org/freedesktop/secrets", "org.freedesktop.Secret.Service")
COLLECTION = "org.freedesktop.Secret.Collection"
# openDatabase runs the KDF on KeePassXC's main thread before replying
TIMEOUT_MS = 60000
DBUS = ("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus")
INI_ESCAPES = dict(zip("abfnrtv\"?'\\", "\a\b\f\n\r\t\v\"?'\\"))


def xdg_dir(var, fallback):
    value = os.environ.get(var, "")
    return Path(value) if value.startswith("/") else Path.home() / fallback


# Where KeePassXC keeps keepassxc.ini: the state dir, the cache dir before it moved, Flatpak and Snap homes
def ini_candidates():
    if override := os.environ.get("KPXC_CONFIG_LOCAL"):
        return [Path(override)]
    home = Path.home()
    return [
        xdg_dir("XDG_STATE_HOME", ".local/state") / "keepassxc/keepassxc.ini",
        xdg_dir("XDG_CACHE_HOME", ".cache") / "keepassxc/keepassxc.ini",
        home / ".var/app" / APP_ID / ".local/state/keepassxc/keepassxc.ini",
        home / ".var/app" / APP_ID / "cache/keepassxc/keepassxc.ini",
        home / "snap/keepassxc/current/.local/state/keepassxc/keepassxc.ini",
        home / "snap/keepassxc/current/.cache/keepassxc/keepassxc.ini",
    ]


def utf16_units_to_str(s):
    return s.encode("utf-16-le", "surrogatepass").decode("utf-16-le", "replace")


# QSettingsPrivate::iniUnescapedStringList: commas split unless quoted, C escapes,
# \x and octal UTF-16 units (Qt 5 wrote non-ASCII that way), unquoted values lose trailing blanks
def qsettings_list(raw):
    items, cur, keep = [], "", 0
    quoted = in_quotes = False
    i, n = 0, len(raw)

    def skip_blanks(i):
        while i < n and raw[i] in " \t":
            i += 1
        return i

    def finish(s):
        return utf16_units_to_str(s if quoted else s[:keep] + s[keep:].rstrip(" \t"))

    i = skip_blanks(0)
    while i < n:
        ch = raw[i]
        i += 1
        if ch == "\\":
            if i == n:
                break
            ch = raw[i]
            i += 1
            if ch in INI_ESCAPES:
                cur += INI_ESCAPES[ch]
            elif ch == "x" or ch in string.octdigits:
                base, digits = (16, string.hexdigits) if ch == "x" else (8, string.octdigits)
                start = i if ch == "x" else i - 1
                while i < n and raw[i] in digits:
                    i += 1
                if i > start:
                    cur += chr(int(raw[start:i], base) & 0xFFFF)
            keep = len(cur)
        elif ch == '"':
            quoted = True
            in_quotes = not in_quotes
            if not in_quotes:
                i = skip_blanks(i)
        elif ch == "," and not in_quotes:
            items.append(finish(cur))
            cur, keep, quoted = "", 0, False
            i = skip_blanks(i)
        else:
            cur += ch
    items.append(finish(cur))
    return items


def last_opened_databases():
    existing = [p for p in ini_candidates() if p.is_file()]
    if not existing:
        return []
    ini = max(existing, key=lambda p: p.stat().st_mtime)
    try:
        lines = ini.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    section = ""
    for line in lines:
        line = line.strip()
        if line.startswith("["):
            section = line
            continue
        key, sep, value = line.partition("=")
        if section == "[General]" and sep and key.strip() == "LastOpenedDatabases":
            return [p for p in qsettings_list(value.strip()) if p.startswith("/")]
    return []


def call(bus, name, path, iface, method, args):
    return bus.call_sync(name, path, iface, method, args, None, Gio.DBusCallFlags.NONE, TIMEOUT_MS, None).unpack()


def keepassxc_running(bus):
    return call(bus, *DBUS, "NameHasOwner", GLib.Variant("(s)", (BUS_NAME,)))[0]


def owner(bus, name):
    return call(bus, *DBUS, "GetNameOwner", GLib.Variant("(s)", (name,)))[0]


def secrets_prop(bus, path, iface, prop):
    args = GLib.Variant("(ss)", (iface, prop))
    return call(bus, SECRETS[0], path, "org.freedesktop.DBus.Properties", "Get", args)[0]


# openDatabase replies the same whether the unlock worked, failed or was ignored.
# KeePassXC labels a locked collection with the file's completeBaseName, which is Path.stem
def still_locked(bus, databases):
    stems = {Path(db).stem for db in databases}
    try:
        if owner(bus, SECRETS[0]) != owner(bus, BUS_NAME):
            return []
        paths = secrets_prop(bus, SECRETS[1], SECRETS[2], "Collections")
        locked = [p for p in paths if secrets_prop(bus, p, COLLECTION, "Locked")]
        return [label for label in (secrets_prop(bus, p, COLLECTION, "Label") for p in locked) if label in stems]
    except GLib.Error:
        return []


def main():
    databases = last_opened_databases()
    if sys.argv[1:] == ["--list"]:
        print("\n".join(databases))
        return 0
    password = sys.stdin.read()
    if not password:
        return 1
    if not databases:
        return 0
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    if not keepassxc_running(bus):
        return 0
    failed = 0
    for db in databases:
        try:
            call(bus, BUS_NAME, "/keepassxc", BUS_NAME, "openDatabase", GLib.Variant("(ss)", (db, password)))
        except GLib.Error as e:
            print(f"keepassxc_unlock_failed db={db} error={e.message}", file=sys.stderr)
            failed = 1
    for label in still_locked(bus, databases):
        print(f"keepassxc_unlock_still_locked collection={label}", file=sys.stderr)
        failed = 1
    return failed


sys.exit(main())
