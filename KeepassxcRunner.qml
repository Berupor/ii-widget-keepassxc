pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

/** Runs unlock.py with the password on stdin, alive after the hook object is gone. */
Singleton {
    id: root

    readonly property string script: decodeURIComponent(Qt.resolvedUrl("unlock.py").toString().replace(/^file:\/\//, ""))
    property list<string> command: ["python3", "-I", root.script]
    property string pending: ""

    function unlock(password: string): void {
        root.pending = password;
        if (!proc.running) {
            proc.stdinEnabled = true;
            proc.running = true;
        }
    }

    Process {
        id: proc
        command: root.command
        onStarted: {
            proc.write(root.pending);
            root.pending = "";
            proc.stdinEnabled = false; // Closes stdin, the script reads to EOF
        }
        onExited: exitCode => {
            if (exitCode !== 0)
                console.error(`keepassxc_unlock_exited code=${exitCode} stderr=${stderrCollector.text.trim()}`);
            if (root.pending !== "")
                root.unlock(root.pending);
        }
        // A failed start emits neither started nor exited, only this
        onRunningChanged: {
            if (!proc.running && root.pending !== "") {
                console.error(`keepassxc_unlock_start_failed command=${root.command[0]}`);
                root.pending = "";
            }
        }
        stderr: StdioCollector {
            id: stderrCollector
        }
    }
}
