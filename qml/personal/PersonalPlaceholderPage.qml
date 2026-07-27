import QtQuick
import QtQuick.Layouts
import "."

Item {
    id: root
    property string pageTitle: ""
    property string pageDescription: ""
    property string symbol: "◌"

    Column {
        width: Math.min(560, parent.width - 60)
        anchors.centerIn: parent
        spacing: 16

        Text {
            text: root.symbol
            color: PersonalTheme.accent
            font.family: PersonalTheme.bodyFont
            font.pixelSize: 34
            anchors.horizontalCenter: parent.horizontalCenter
        }
        Text {
            width: parent.width
            text: root.pageTitle
            color: PersonalTheme.text
            horizontalAlignment: Text.AlignHCenter
            font.family: PersonalTheme.displayFont
            font.pixelSize: 32
        }
        Text {
            width: parent.width
            text: root.pageDescription
            color: PersonalTheme.muted
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            lineHeight: 1.35
            font.family: PersonalTheme.bodyFont
            font.pixelSize: 13
        }
    }
}
