import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Item {
    id: root
    property bool animationEnabled: true

    RowLayout {
        anchors.fill: parent
        spacing: 16

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: 620
            spacing: 14

            GlassPanel {
                Layout.fillWidth: true
                Layout.fillHeight: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 22
                    spacing: 14

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "ИСТОРИЯ КОМАНД"
                            color: Theme.text
                            font.family: Theme.headingFont
                            font.pixelSize: 17
                            font.weight: Font.DemiBold
                            font.letterSpacing: 0.7
                        }
                        Item { Layout.fillWidth: true }
                        Rectangle {
                            width: 88
                            height: 26
                            radius: 13
                            color: "#182B5A"
                            Text {
                                anchors.centerIn: parent
                                text: backend.historyItems.length + " / 100"
                                color: Theme.muted
                                font.family: Theme.monoFont
                                font.pixelSize: 10
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Theme.border
                    }

                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        Column {
                            visible: backend.historyItems.length === 0
                            anchors.centerIn: parent
                            spacing: 8
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "Команд пока нет"
                                color: Theme.text
                                font.family: Theme.bodyFont
                                font.pixelSize: 17
                                font.weight: Font.DemiBold
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "Введите название программы или команду ниже."
                                color: Theme.muted
                                font.family: Theme.bodyFont
                                font.pixelSize: 13
                            }
                        }

                        ListView {
                            id: historyList
                            anchors.fill: parent
                            visible: count > 0
                            model: backend.historyItems
                            spacing: 9
                            clip: true
                            boundsBehavior: Flickable.StopAtBounds
                            ScrollBar.vertical: ScrollBar {
                                policy: ScrollBar.AsNeeded
                            }
                            onCountChanged: Qt.callLater(positionViewAtEnd)

                            delegate: Rectangle {
                                id: historyCard
                                required property var modelData
                                width: historyList.width - 12
                                height: 70
                                radius: 13
                                color: hover.hovered ? "#C0162C59" : "#9B0B1937"
                                border.width: 1
                                border.color: hover.hovered ? Theme.borderStrong : "#345B82BC"

                                readonly property color statusColor: modelData.status === "success" ? Theme.success
                                                                           : modelData.status === "error" || modelData.status === "not_found" ? Theme.danger
                                                                           : modelData.status === "pending" ? Theme.warning
                                                                           : Theme.accent

                                HoverHandler { id: hover }

                                Rectangle {
                                    width: 3
                                    height: 34
                                    radius: 2
                                    color: historyCard.statusColor
                                    anchors.left: parent.left
                                    anchors.leftMargin: 12
                                    anchors.verticalCenter: parent.verticalCenter
                                }

                                Column {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 28
                                    anchors.right: removeButton.left
                                    anchors.rightMargin: 10
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: 4
                                    Text {
                                        width: parent.width
                                        text: modelData.command
                                        color: Theme.text
                                        elide: Text.ElideRight
                                        font.family: Theme.monoFont
                                        font.pixelSize: 12
                                        font.weight: Font.DemiBold
                                    }
                                    Text {
                                        width: parent.width
                                        text: modelData.title + (modelData.detail ? "  ·  " + modelData.detail : "")
                                        color: Theme.muted
                                        elide: Text.ElideRight
                                        font.family: Theme.bodyFont
                                        font.pixelSize: 12
                                    }
                                }

                                Rectangle {
                                    id: removeButton
                                    width: 30
                                    height: 30
                                    radius: 9
                                    color: removeHover.hovered ? "#2AFF5D6C" : "transparent"
                                    anchors.right: parent.right
                                    anchors.rightMargin: 14
                                    anchors.verticalCenter: parent.verticalCenter
                                    Accessible.role: Accessible.Button
                                    Accessible.name: "Удалить запись из истории"
                                    Text {
                                        anchors.centerIn: parent
                                        text: "×"
                                        color: removeHover.hovered ? Theme.danger : Theme.muted
                                        font.pixelSize: 19
                                    }
                                    HoverHandler { id: removeHover }
                                    TapHandler { onTapped: backend.removeHistory(modelData.id) }
                                }
                            }
                        }
                    }
                }
            }

            GlassPanel {
                Layout.fillWidth: true
                Layout.preferredHeight: 112

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        TextField {
                            id: commandField
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            leftPadding: 18
                            rightPadding: 18
                            color: Theme.text
                            selectionColor: Theme.primary
                            selectedTextColor: Theme.text
                            placeholderText: "Что запустить?"
                            placeholderTextColor: "#7388B2"
                            font.family: Theme.bodyFont
                            font.pixelSize: 15
                            enabled: !backend.busy
                            Accessible.name: "Команда JARVIS"
                            background: Rectangle {
                                radius: 13
                                color: "#CC06132E"
                                border.width: commandField.activeFocus ? 1.5 : 1
                                border.color: commandField.activeFocus ? Theme.accent : Theme.border
                            }
                            onAccepted: {
                                if (text.trim().length > 0) {
                                    backend.executeCommand(text)
                                    text = ""
                                }
                            }
                        }

                        Rectangle {
                            id: sendButton
                            width: 50
                            height: 48
                            radius: 13
                            color: backend.busy ? "#27477D" : (sendHover.hovered ? Theme.accent : Theme.primary)
                            Accessible.role: Accessible.Button
                            Accessible.name: "Выполнить команду"
                            Text {
                                anchors.centerIn: parent
                                text: backend.busy ? "···" : "→"
                                color: Theme.text
                                font.family: Theme.headingFont
                                font.pixelSize: backend.busy ? 16 : 22
                                font.weight: Font.DemiBold
                            }
                            HoverHandler { id: sendHover }
                            TapHandler {
                                enabled: !backend.busy
                                onTapped: commandField.accepted()
                            }
                        }
                    }

                    Row {
                        spacing: 14
                        Text {
                            text: "/help"
                            color: Theme.accent
                            font.family: Theme.monoFont
                            font.pixelSize: 10
                        }
                        Text {
                            text: "/apps"
                            color: Theme.muted
                            font.family: Theme.monoFont
                            font.pixelSize: 10
                        }
                        Text {
                            text: "/game"
                            color: Theme.muted
                            font.family: Theme.monoFont
                            font.pixelSize: 10
                        }
                        Text {
                            text: "Ctrl + K — перейти к команде"
                            color: "#657AA4"
                            font.family: Theme.bodyFont
                            font.pixelSize: 10
                        }
                    }
                }

                Shortcut {
                    sequence: "Ctrl+K"
                    onActivated: commandField.forceActiveFocus()
                }
            }
        }

        JarvisCore {
            Layout.fillHeight: true
            Layout.preferredWidth: 386
            Layout.minimumWidth: 320
            state: backend.jarvisState
            stateLabel: backend.stateLabel
            reducedMotion: backend.reducedMotion
            animationEnabled: root.animationEnabled
        }
    }
}
