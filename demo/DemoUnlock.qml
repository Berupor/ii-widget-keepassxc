//@ probe keepassxc -g 40x40 -s 3000
import ".."
import QtQuick
import Quickshell.Io

/**
 * The runner on a stand-in script that appends stdin to a file: each password arrives whole,
 * one that comes while a run is going waits for it, and a command that cannot start drops it.
 */
Item {
    id: probe

    property string out: ""
    property bool runningAfterSecond: false
    property string pendingAfterFailedStart: "unset"

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
                "name": "the second unlock came while the first was running",
                "got": probe.runningAfterSecond,
                "want": true
            },
            {
                "name": "both passwords reach the script whole, in order",
                "got": received.text,
                "want": "pass word\nsecond one\n"
            },
            {
                "name": "a command that cannot start does not keep the password",
                "got": probe.pendingAfterFailedStart,
                "want": ""
            }
        ];
    }

    Process {
        running: true
        command: ["mktemp"]
        stdout: StdioCollector {
            onStreamFinished: {
                probe.out = text.trim();
                KeepassxcRunner.command = ["sh", "-c", 'cat >> "$0"; echo >> "$0"; sleep 0.3', probe.out];
                KeepassxcRunner.unlock("pass word");
                second.start();
            }
        }
    }

    // After the first run has started and taken its password
    Timer {
        id: second
        interval: 100
        onTriggered: {
            KeepassxcRunner.unlock("second one");
            probe.runningAfterSecond = KeepassxcRunner.pending === "second one";
            collect.start();
        }
    }

    Timer {
        id: collect
        interval: 1200
        onTriggered: {
            read.running = true;
            KeepassxcRunner.command = ["/nonexistent/keepassxc-demo"];
            KeepassxcRunner.unlock("lost");
            failed.start();
        }
    }

    Timer {
        id: failed
        interval: 300
        onTriggered: probe.pendingAfterFailedStart = KeepassxcRunner.pending
    }

    Process {
        id: read
        command: ["sh", "-c", 'cat "$0"; rm -f "$0"', probe.out]
        stdout: StdioCollector {
            id: received
        }
    }
}
