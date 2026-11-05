# KeePassXC unlock

A widget for the [illogical-impulse extensions
fork](https://github.com/Berupor/dots-hyprland-extensions): unlocking the lock
screen with your password also unlocks the KeePassXC databases that were open in
its last session. Only useful when they share the login password. Nothing to
draw: it hangs on the `unlockHook` slot, contract 1.5.

The list comes from `LastOpenedDatabases` in
`~/.local/state/keepassxc/keepassxc.ini`, written when KeePassXC exits, so a
database first opened in the current session is not in it yet. Older releases
kept that file in `~/.cache/keepassxc/`, Flatpak and Snap under their own homes;
the newest one found wins, and `KPXC_CONFIG_LOCAL` overrides the search.

The password goes to `unlock.py` on stdin and from there to KeePassXC's
`openDatabase` over the session bus, where any process of your user can watch
it. A fingerprint unlock has no password to hand, so KeePassXC stays locked. If
KeePassXC is not running, nothing happens. Turn off "Prompt to unlock database
before searching" (Settings, Secret Service Integration): a secret lookup on a
locked database opens an unlock dialog and blocks until it closes, and KeePassXC
drops unlock requests meanwhile.
`openDatabase` does not report a wrong password, so afterwards the script checks
the Secret Service collections and logs `keepassxc_unlock_still_locked` for the
listed databases still locked. Other databases you keep locked are left alone.

Needs `keepassxc` and `python3` with PyGObject (`python-gobject` on Arch); the
card greys out without them.

## Install

Paste `https://github.com/Berupor/ii-widget-keepassxc` on the Widgets page, or
clone it into `~/.config/illogical-impulse/widgets/keepassxc/` (the folder name
has to be `keepassxc`), then enable it.
