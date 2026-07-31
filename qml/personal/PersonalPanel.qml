import QtQuick
import "."

Rectangle {
    id: root
    default property alias content: contentItem.data
    property alias contentItem: contentItem
    property bool elevated: false

    radius: PersonalTheme.radiusMedium
    color: elevated ? PersonalTheme.surfaceRaised : PersonalTheme.surface
    border.width: 1
    border.color: PersonalTheme.border

    Item {
        id: contentItem
        anchors.fill: parent
    }
}
