import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            Column {
                spacing: 3
                LabelSmooth {
                    text: "ИГРОВОЙ РЕЖИМ"
                    color: Theme.text
                    font.family: Theme.headingFont
                    font.pixelSize: Theme.hero
                    font.weight: Font.DemiBold
                    font.letterSpacing: 0.8
                }
                LabelSharp {
                    text: "Освободите ресурсы перед запуском игры"
                    color: Theme.muted
                    font.family: Theme.bodyFont
                    font.pixelSize: Theme.body
                }
            }
            Item { Layout.fillWidth: true }
            ActionButton {
                text: backend.busy ? "Сканирую…" : "Проверить"
                enabled: !backend.busy
                onClicked: backend.previewGameMode()
            }
            ActionButton {
                text: "Протокол игры"
                accent: true
                enabled: !backend.busy
                onClicked: backend.activateGameMode()
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            GlassPanel {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.right: sidePanel.left
                anchors.rightMargin: 14
                anchors.bottom: parent.bottom

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 13

                    RowLayout {
                        Layout.fillWidth: true
                        LabelSmooth {
                            text: "НАЙДЕННЫЕ ПРОЦЕССЫ"
                            color: Theme.text
                            font.family: Theme.headingFont
                            font.pixelSize: Theme.title
                            font.weight: Font.DemiBold
                        }
                        Item { Layout.fillWidth: true }
                        Rectangle {
                            width: 38
                            height: 26
                            radius: 13
                            color: backend.gameCandidates.length > 0 ? "#2CF3B85B" : "#18345F"
                            LabelSharp {
                                anchors.centerIn: parent
                                text: backend.gameCandidates.length
                                color: backend.gameCandidates.length > 0 ? Theme.warning : Theme.muted
                                font.family: Theme.monoFont
                                font.pixelSize: Theme.caption
                                font.weight: Font.Bold
                            }
                        }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }

                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        Column {
                            visible: backend.gameCandidates.length === 0
                            anchors.centerIn: parent
                            spacing: 9
                            Rectangle {
                                width: 56
                                height: 56
                                radius: 18
                                color: "#2538A7FF"
                                anchors.horizontalCenter: parent.horizontalCenter
                                Image {
                                    anchors.centerIn: parent
                                    source: Qt.resolvedUrl("../../assets/icons/game.svg")
                                    sourceSize.width: 26
                                    sourceSize.height: 26
                                }
                            }
                            LabelSmooth {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "Сначала выполните проверку"
                                color: Theme.text
                                font.family: Theme.bodyFont
                                font.pixelSize: Theme.title
                                font.weight: Font.DemiBold
                            }
                            LabelSharp {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "Supersonic покажет браузеры и приложения с заметной GPU-нагрузкой."
                                color: Theme.muted
                                font.family: Theme.bodyFont
                                font.pixelSize: Theme.label
                            }
                        }

                        ListView {
                            id: processList
                            anchors.fill: parent
                            visible: backend.gameCandidates.length > 0
                            model: backend.gameCandidates
                            spacing: 9
                            clip: true
                            boundsBehavior: Flickable.StopAtBounds
                            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                            delegate: Rectangle {
                                required property var modelData
                                width: processList.width - 12
                                height: 64
                                radius: 13
                                color: "#A00C1C3D"
                                border.width: 1
                                border.color: Theme.border

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 15
                                    anchors.rightMargin: 15
                                    Rectangle {
                                        width: 34
                                        height: 34
                                        radius: 11
                                        color: "#2CF3B85B"
                                        LabelSmooth {
                                            anchors.centerIn: parent
                                            text: "!"
                                            color: Theme.warning
                                            font.family: Theme.headingFont
                                            font.pixelSize: Theme.title
                                            font.weight: Font.Bold
                                        }
                                    }
                                    Column {
                                        Layout.fillWidth: true
                                        spacing: 3
                                        LabelSharp {
                                            width: parent.width
                                            text: modelData.name
                                            color: Theme.text
                                            elide: Text.ElideRight
                                            font.family: Theme.bodyFont
                                            font.pixelSize: Theme.body
                                            font.weight: Font.DemiBold
                                        }
                                        LabelSharp {
                                            text: modelData.reason
                                            color: Theme.muted
                                            font.family: Theme.bodyFont
                                            font.pixelSize: Theme.caption
                                        }
                                    }
                                    LabelSharp {
                                        text: "PID " + modelData.pid
                                        color: Theme.muted
                                        font.family: Theme.monoFont
                                        font.pixelSize: Theme.micro
                                    }
                                }
                            }
                        }
                    }

                    LabelSharp {
                        Layout.fillWidth: true
                        visible: backend.gameWarning.length > 0
                        text: backend.gameWarning
                        color: Theme.warning
                        wrapMode: Text.WordWrap
                        font.family: Theme.bodyFont
                        font.pixelSize: Theme.caption
                    }
                }
            }

            ColumnLayout {
                id: sidePanel
                width: 286
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                spacing: 14

                GlassPanel {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 198

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 10
                        LabelSharp {
                            text: "ЗАВЕРШИТЬ ПРИЛОЖЕНИЕ"
                            color: Theme.muted
                            font.family: Theme.monoFont
                            font.pixelSize: Theme.micro
                            font.letterSpacing: 1.1
                        }
                        LabelSharp {
                            Layout.fillWidth: true
                            text: "Supersonic найдёт процесс и покажет точное дерево перед завершением."
                            color: Theme.text
                            wrapMode: Text.WordWrap
                            font.family: Theme.bodyFont
                            font.pixelSize: Theme.label
                        }
                        TextField {
                            id: killField
                            Layout.fillWidth: true
                            Layout.preferredHeight: 42
                            leftPadding: 14
                            rightPadding: 14
                            color: Theme.text
                            placeholderText: "Например, chrome"
                            placeholderTextColor: "#7388B2"
                            font.family: Theme.bodyFont
                            font.pixelSize: Theme.body
                            renderType: Text.NativeRendering
                            Accessible.name: "Название процесса для завершения"
                            background: Rectangle {
                                radius: 11
                                color: "#B4081734"
                                border.width: killField.activeFocus ? 2 : 1
                                border.color: killField.activeFocus ? Theme.accent : Theme.border

                                Behavior on border.width {
                                    NumberAnimation { duration: Theme.durFocus; easing.type: Theme.easeOut }
                                }
                                Behavior on border.color {
                                    ColorAnimation { duration: Theme.durFocus }
                                }
                            }
                            onAccepted: killButton.clicked()
                        }
                        ActionButton {
                            id: killButton
                            Layout.fillWidth: true
                            text: "Найти процесс"
                            enabled: killField.text.trim().length > 0 && !backend.busy
                            onClicked: backend.runKill(killField.text)
                        }
                    }
                }

                GlassPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 11
                        LabelSharp {
                            text: "ЗАЩИТА"
                            color: Theme.muted
                            font.family: Theme.monoFont
                            font.pixelSize: Theme.micro
                            font.letterSpacing: 1.1
                        }
                        LabelSharp {
                            Layout.fillWidth: true
                            text: "Системные процессы Windows, NVIDIA, Supersonic, Steam, Epic Games Launcher и игровые процессы не закрываются."
                            color: Theme.text
                            wrapMode: Text.WordWrap
                            font.family: Theme.bodyFont
                            font.pixelSize: Theme.label
                            lineHeight: Theme.lineHeightRelaxed
                        }
                        Item { Layout.fillHeight: true }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 46
                            radius: 12
                            color: "#1E42D392"
                            border.width: 1
                            border.color: "#5942D392"
                            Row {
                                anchors.centerIn: parent
                                spacing: 9
                                Rectangle { width: 8; height: 8; radius: 4; color: Theme.success; anchors.verticalCenter: parent.verticalCenter }
                                LabelSharp {
                                    text: "Защита активна"
                                    color: Theme.success
                                    font.family: Theme.bodyFont
                                    font.pixelSize: Theme.label
                                    font.weight: Font.DemiBold
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
