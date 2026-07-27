import QtQuick
import ".."

Rectangle {
    id: root
    default property alias content: contentItem.data
    property alias contentItem: contentItem
    radius: 18
    color: Theme.panel
    border.width: 1
    border.color: Theme.border

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 1
        height: 1
        radius: 1
        color: "#4AFFFFFF"
    }

    Item {
        id: contentItem
        anchors.fill: parent
    }
}
