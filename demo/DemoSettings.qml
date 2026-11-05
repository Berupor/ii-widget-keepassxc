//@ probe keepassxc -g 420x110 -s 2500
import ".."
import QtQuick
import Quickshell.Io
import qs.modules.common
import qs.modules.common.functions

/** The card body lists what the script would unlock, read from a keepassxc.ini the way Qt writes it. */
Item {
    readonly property string home: FileUtils.trimFileProtocol(Directories.home).replace(/\/+$/, "")
    // demo/keepassxc.ini: written by QSettings from Qt 6, plus two entries in Qt 5's \x escapes
    readonly property list<string> written: ["/home/u/a, b.kdbx", "/home/u/q\"uote.kdbx", "/home/u/Пароли.kdbx", "/home/u/back\\slash.kdbx", "/home/u/ trail .kdbx", "/home/u/semi;colon.kdbx", "/home/u/😀.kdbx", "/home/u/@at.kdbx", "/home/u/tab\t.kdbx", "/home/u/plain.kdbx", "/home/u/Пароль1.kdbx", "/home/u/😀.kdbx"]

    function checks() {
        return [
            {
                "name": "the card gets the list back from the script",
                "got": page.loaded,
                "want": true
            },
            {
                "name": "a path under home is shortened",
                "got": page.shortPath(home + "/db/x.kdbx"),
                "want": "~/db/x.kdbx"
            },
            {
                "name": "a sibling of home sharing its prefix is not",
                "got": page.shortPath(home + "b/x.kdbx"),
                "want": home + "b/x.kdbx"
            },
            {
                "name": "home inside a path is not",
                "got": page.shortPath("/mnt" + home + "/x.kdbx"),
                "want": "/mnt" + home + "/x.kdbx"
            },
            {
                "name": "the script reads every path QSettings wrote",
                "got": parsed.text,
                "want": written.join("\n") + "\n"
            }
        ];
    }

    KeepassxcSettings {
        id: page
        anchors.fill: parent
        anchors.margins: 8
    }

    Process {
        running: true
        command: ["python3", "-I", KeepassxcRunner.script, "--list"]
        environment: ({
                "KPXC_CONFIG_LOCAL": decodeURIComponent(Qt.resolvedUrl("keepassxc.ini").toString().replace(/^file:\/\//, ""))
            })
        stdout: StdioCollector {
            id: parsed
        }
    }
}
