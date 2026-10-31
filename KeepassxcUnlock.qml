import QtQuick

QtObject {
    function unlocked(password: string): void {
        KeepassxcRunner.unlock(password);
    }
}
