//@ probe keepassxc -g 420x110 -s 2500
import ".."
import QtQuick

/** The card body lists what the script would unlock. */
Item {
    function checks() {
        return [
            {
                "name": "the list comes back from the script",
                "got": page.loaded,
                "want": true
            },
            {
                "name": "paths under home are shortened",
                "got": page.databases.every(p => !p.startsWith("/home/")),
                "want": true
            }
        ];
    }

    KeepassxcSettings {
        id: page
        anchors.fill: parent
        anchors.margins: 8
    }
}
