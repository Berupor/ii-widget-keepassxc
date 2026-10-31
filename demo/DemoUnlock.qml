//@ probe keepassxc -g 40x40 -s 1500
import ".."
import QtQuick
import Quickshell.Io

/** The runner finds its script as a plain path, and stdin closes after the password. */
Item {
    id: probe

    function checks() {
        return [
            {
                "name": "script path is absolute",
                "got": KeepassxcRunner.script.startsWith("/"),
                "want": true
            },
            {
                "name": "and points at unlock.py",
                "got": KeepassxcRunner.script.endsWith("/unlock.py"),
                "want": true
            },
            {
                "name": "a reader to EOF gets the password whole and exits",
                "got": echo.text,
                "want": "pass word"
            }
        ];
    }

    // The same write-then-close sequence as KeepassxcRunner, on cat
    Process {
        id: cat
        running: true
        stdinEnabled: true
        command: ["cat"]
        onStarted: {
            cat.write("pass word");
            cat.stdinEnabled = false;
        }
        stdout: StdioCollector {
            id: echo
        }
    }
}
