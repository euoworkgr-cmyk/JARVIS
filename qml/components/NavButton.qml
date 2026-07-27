import QtQuick
import QtQuick.Controls
import ".."

Rectangle {
    id: root
    required property url iconSource
    property string label: ""
    property bool selected: false
    signal clicked()

    width: 48
    height: 48
    radius: 14
    color: selected ? "#3A276FD8" : (hover.hovered ? "#221E63BC" : "transparent")
    border.width: selected ? 1 : 0
    border.color: selected ? Theme.borderStrong : "transparent"
    Accessible.role: Accessible.Button
    Accessible.name: label

    Rectangle {
        visible: root.selected
        width: 3
        height: 22
        radius: 2
        color: Theme.accent
        anchors.left: parent.left
        anchors.leftMargin: -1
        anchors.verticalCenter: parent.verticalCenter
    }

    Image {
        anchors.centerIn: parent
        source: root.iconSource
        sourceSize.width: 22
        sourceSize.height: 22
        opacity: root.selected || hover.hovered ? 1.0 : 0.68
        fillMode: Image.PreserveAspectFit
    }

    HoverHandler { id: hover }
    TapHandler { onTapped: root.clicked() }

    ToolTip.visible: hover.hovered
    ToolTip.text: root.label
    ToolTip.delay: 450
}
