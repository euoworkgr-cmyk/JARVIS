import QtQuick
import QtQuick.Controls
import "."

ScrollBar {
    id: control
    implicitWidth: 8
    implicitHeight: 8
    padding: 2

    contentItem: Rectangle {
        implicitWidth: 4
        implicitHeight: 40
        radius: 2
        color: control.pressed || control.hovered
               ? PersonalTheme.borderStrong : PersonalTheme.border
        opacity: control.policy === ScrollBar.AlwaysOff || control.size >= 1 ? 0 : 1

        Behavior on color {
            ColorAnimation { duration: PersonalTheme.durFast }
        }
        Behavior on opacity {
            NumberAnimation { duration: PersonalTheme.durFast }
        }
    }

    background: Item { }
}
