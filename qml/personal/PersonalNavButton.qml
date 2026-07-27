import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import ".." as Shared

Button {
    id: root
    required property string iconName
    required property string label
    property bool selected: false

    implicitWidth: 160
    implicitHeight: 56
    hoverEnabled: true
    activeFocusOnTab: true
    padding: 0
    Accessible.name: label

    background: Rectangle {
        radius: PersonalTheme.radiusSmall
        color: root.down ? PersonalTheme.surfaceRaised
                         : root.selected ? PersonalTheme.accentGhost
                         : root.hovered ? PersonalTheme.surface : "transparent"
        border.width: root.activeFocus ? 1 : (root.selected ? 1 : 0)
        border.color: root.activeFocus ? PersonalTheme.accent
                                       : root.selected ? PersonalTheme.borderStrong : "transparent"

        Behavior on color {
            ColorAnimation { duration: PersonalTheme.durFast }
        }

    }

    contentItem: RowLayout {
        spacing: 11

        Item {
            Layout.leftMargin: 13
            Layout.preferredWidth: 24
            Layout.preferredHeight: 24

            PersonalIcon {
                anchors.fill: parent
                name: root.iconName
                color: root.selected || root.hovered ? PersonalTheme.text : PersonalTheme.muted
            }
        }

        Shared.LabelSharp {
            text: root.label
            color: root.selected ? PersonalTheme.text : PersonalTheme.muted
            font.family: PersonalTheme.bodyFont
            font.pixelSize: PersonalTheme.body
            font.weight: root.selected ? Font.DemiBold : Font.Normal
            Layout.fillWidth: true
            verticalAlignment: Text.AlignVCenter
        }

    }
}
