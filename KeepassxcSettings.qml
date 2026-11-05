import QtQuick
import QtQuick.Layouts
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.functions
import qs.modules.common.widgets

ColumnLayout {
    id: root

    property list<string> databases: []
    property bool loaded: false

    Process {
        running: true
        command: ["python3", "-I", KeepassxcRunner.script, "--list"]
        stdout: StdioCollector {
            onStreamFinished: {
                const home = FileUtils.trimFileProtocol(Directories.home).replace(/\/+$/, "");
                root.databases = text.split("\n").filter(p => p !== "").map(p => p.startsWith(home + "/") ? "~" + p.slice(home.length) : p);
                root.loaded = true;
            }
        }
    }

    ContentSubsection {
        title: Translation.tr("Unlocks")

        StyledText {
            Layout.fillWidth: true
            Layout.leftMargin: 2
            text: !root.loaded ? "" : root.databases.length > 0 ? root.databases.join("\n")
                : Translation.tr("Nothing yet: KeePassXC lists the databases it had open when it last exited")
            color: root.databases.length > 0 ? Appearance.colors.colOnLayer1 : Appearance.colors.colSubtext
            wrapMode: Text.WordWrap
        }
    }
}
