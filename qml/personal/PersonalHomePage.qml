import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: root

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: content.implicitHeight + 48
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        Item {
            id: content
            width: parent.width
            implicitHeight: pageColumn.implicitHeight

            TopoBackground {
                width: parent.width * 0.72
                height: 390
                anchors.right: parent.right
                anchors.top: parent.top
            }

            ColumnLayout {
                id: pageColumn
                width: parent.width
                spacing: 22

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 220

                    Column {
                        anchors.left: parent.left
                        anchors.leftMargin: 8
                        anchors.top: parent.top
                        anchors.topMargin: 28
                        width: Math.min(720, parent.width * 0.78)
                        spacing: 18

                        Text {
                            width: parent.width
                            text: "Привет, " + backend.displayName + "!\nКак я могу помочь?"
                            color: PersonalTheme.text
                            font.family: PersonalTheme.displayFont
                            font.pixelSize: 40
                            font.weight: Font.Normal
                            lineHeight: 1.12
                            wrapMode: Text.WordWrap
                        }

                        Row {
                            spacing: 12

                            Row {
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: 3
                                Repeater {
                                    model: [8, 15, 23, 12, 19, 9]
                                    Rectangle {
                                        required property int modelData
                                        width: 3
                                        height: modelData
                                        radius: 2
                                        color: backend.busy ? PersonalTheme.warning
                                                              : backend.jarvisState === "error" ? PersonalTheme.danger
                                                              : PersonalTheme.accent
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                }
                            }
                            Text {
                                text: backend.stateLabel
                                color: PersonalTheme.accent
                                font.family: PersonalTheme.bodyFont
                                font.pixelSize: 13
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Text {
                        text: "Быстрый запуск"
                        color: PersonalTheme.text
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 5
                        columnSpacing: 12

                        Repeater {
                            model: backend.presetItems

                            Rectangle {
                                id: presetCard
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredHeight: 94
                                radius: PersonalTheme.radiusMedium
                                color: presetHover.hovered ? PersonalTheme.surfaceHover : PersonalTheme.surface
                                border.width: 1
                                border.color: presetHover.hovered ? PersonalTheme.borderStrong : PersonalTheme.border
                                Accessible.role: Accessible.Button
                                Accessible.name: "Запустить " + modelData.title

                                Column {
                                    anchors.centerIn: parent
                                    width: parent.width - 20
                                    spacing: 10

                                    Rectangle {
                                        width: 36
                                        height: 36
                                        radius: 9
                                        color: PersonalTheme.surfaceRaised
                                        border.width: 1
                                        border.color: PersonalTheme.border
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        Text {
                                            anchors.centerIn: parent
                                            text: modelData.monogram
                                            color: PersonalTheme.accent
                                            font.family: PersonalTheme.utilityFont
                                            font.pixelSize: 11
                                            font.weight: Font.DemiBold
                                        }
                                    }
                                    Text {
                                        width: parent.width
                                        text: modelData.title
                                        color: PersonalTheme.text
                                        elide: Text.ElideRight
                                        horizontalAlignment: Text.AlignHCenter
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: 12
                                    }
                                }

                                HoverHandler { id: presetHover }
                                TapHandler {
                                    enabled: !backend.busy
                                    onTapped: backend.launchPreset(modelData.number)
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: PersonalTheme.border
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "Протоколы"
                            color: PersonalTheme.text
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: 17
                            font.weight: Font.DemiBold
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            text: "Персональные команды"
                            color: PersonalTheme.subtle
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: 11
                        }
                    }

                    Repeater {
                        model: backend.protocolItems

                        Rectangle {
                            id: protocolRow
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 56
                            radius: PersonalTheme.radiusSmall
                            color: protocolHover.hovered ? PersonalTheme.surfaceHover : PersonalTheme.surface
                            border.width: 1
                            border.color: protocolHover.hovered ? PersonalTheme.borderStrong : PersonalTheme.border
                            Accessible.role: Accessible.Button
                            Accessible.name: "Запустить протокол " + modelData.title

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 16
                                anchors.rightMargin: 16
                                spacing: 14

                                Text {
                                    text: modelData.symbol
                                    color: PersonalTheme.accent
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: 20
                                    Layout.preferredWidth: 26
                                    horizontalAlignment: Text.AlignHCenter
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    Text {
                                        text: modelData.title
                                        color: PersonalTheme.text
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: 13
                                        font.weight: Font.DemiBold
                                    }
                                    Text {
                                        text: modelData.detail
                                        color: PersonalTheme.muted
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: 11
                                    }
                                }
                                Rectangle {
                                    visible: modelData.extra
                                    width: 44
                                    height: 22
                                    radius: 6
                                    color: "transparent"
                                    border.width: 1
                                    border.color: PersonalTheme.accentMuted
                                    Text {
                                        anchors.centerIn: parent
                                        text: "Extra"
                                        color: PersonalTheme.accent
                                        font.family: PersonalTheme.utilityFont
                                        font.pixelSize: 9
                                    }
                                }
                                Text {
                                    text: "›"
                                    color: PersonalTheme.muted
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: 24
                                }
                            }

                            HoverHandler { id: protocolHover }
                            TapHandler {
                                enabled: !backend.busy
                                onTapped: backend.runProtocol(modelData.id)
                            }
                        }
                    }
                }
            }
        }
    }
}
