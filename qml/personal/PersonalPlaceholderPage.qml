import QtQuick
import QtQuick.Layouts
import "."
import ".." as Shared

Item {
    id: root
    property string pageTitle: ""
    property string pageDescription: ""
    property string symbol: "◌"

    Column {
        width: Math.round(Math.min(560, parent.width - 60))
        anchors.centerIn: parent
        spacing: 16

        Shared.LabelSmooth {
            text: root.symbol
            color: PersonalTheme.accent
            font.family: PersonalTheme.bodyFont
            font.pixelSize: PersonalTheme.hero
            anchors.horizontalCenter: parent.horizontalCenter
        }
        Shared.LabelSmooth {
            width: parent.width
            text: root.pageTitle
            color: PersonalTheme.text
            horizontalAlignment: Text.AlignHCenter
            font.family: PersonalTheme.displayFont
            font.pixelSize: PersonalTheme.hero
        }
        Shared.LabelSharp {
            width: parent.width
            text: root.pageDescription
            color: PersonalTheme.muted
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            lineHeight: PersonalTheme.lineHeightRelaxed
            font.family: PersonalTheme.bodyFont
            font.pixelSize: PersonalTheme.body
        }
    }
}
