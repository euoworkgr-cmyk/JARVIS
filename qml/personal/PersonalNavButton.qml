import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Rectangle {
    id: root
    required property string symbol
    required property string label
    property bool selected: false
    signal clicked()

    implicitWidth: 166
    implicitHeight: 48
    radius: PersonalTheme.radiusSmall
    color: selected ? PersonalTheme.surfaceHover
                    : (hover.hovered ? PersonalTheme.surface : "transparent")
    border.width: selected ? 1 : 0
    border.color: selected ? PersonalTheme.border : "transparent"
    Accessible.role: Accessible.Button
    Accessible.name: label

    Rectangle {
        visible: root.selected
        width: 3
        height: 24
        radius: 2
        color: PersonalTheme.accent
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 15
        anchors.rightMargin: 12
        spacing: 12

        Text {
            text: root.symbol
            color: root.selected ? PersonalTheme.accent : PersonalTheme.muted
            font.family: PersonalTheme.bodyFont
            font.pixelSize: 20
            horizontalAlignment: Text.AlignHCenter
            Layout.preferredWidth: 24
        }
        Text {
            text: root.label
            color: root.selected ? PersonalTheme.text : PersonalTheme.muted
            font.family: PersonalTheme.bodyFont
            font.pixelSize: 13
            font.weight: root.selected ? Font.DemiBold : Font.Normal
            Layout.fillWidth: true
        }
    }

    HoverHandler { id: hover }
    TapHandler { onTapped: root.clicked() }
}
