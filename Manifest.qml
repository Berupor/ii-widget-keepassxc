import qs.modules.widgets
import qs.services
import Quickshell.Io

WidgetManifest {
    id: root
    widgetId: "keepassxc"
    name: Translation.tr("KeePassXC unlock")
    description: Translation.tr("Unlocking the screen also unlocks KeePassXC, for databases sharing the login password")
    icon: "passkey"
    version: "1.2"
    author: "Berupor"
    minShellVersion: "1.5"
    dependencies: ["keepassxc", "python3"]
    slots: ({ "unlockHook": "KeepassxcUnlock.qml" })
    settingsPage: "KeepassxcSettings.qml"

    property bool hasGi: false
    available: depsChecked && depsMissing.length === 0 && hasGi
    property Process giCheck: Process {
        running: true
        command: ["python3", "-I", "-c", "import gi"]
        onExited: exitCode => root.hasGi = exitCode === 0
    }
}
