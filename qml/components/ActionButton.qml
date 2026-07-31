import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: root
    property bool accent: false
    property bool danger: false
    property string accessibleName: text

    implicitHeight: 42
    leftPadding: 18
    rightPadding: 18
    Accessible.name: accessibleName

    scale: root.down ? 0.97 : root.hovered ? 1.015 : 1
    Behavior on scale {
        NumberAnimation {
            duration: Theme.durFast
            easing.type: Theme.easeOut
        }
    }

    contentItem: LabelSmooth {
        text: root.text
        color: Theme.text
        font.family: Theme.bodyFont
        font.pixelSize: Theme.body
        font.weight: root.accent ? Font.DemiBold : Font.Normal
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        radius: 12
        color: !root.enabled ? "#27477D"
             : root.danger ? (root.hovered ? "#D14A5668" : "#A5344056")
             : root.accent ? (root.hovered ? Theme.accent : Theme.primary)
             : root.hovered ? "#263D70" : "#192B51"
        border.width: root.accent ? 0 : 1
        border.color: root.danger ? "#70FF5D6C" : Theme.border
        Behavior on color { ColorAnimation { duration: Theme.durFast } }
    }
}
