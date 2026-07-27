import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: root

    function resourceItems() {
        return [
            backend.systemStats.cpu,
            backend.systemStats.gpu,
            backend.systemStats.memory
        ]
    }

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: pageColumn.implicitHeight + 40
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        ColumnLayout {
            id: pageColumn
            width: parent.width
            spacing: 22

            RowLayout {
                Layout.fillWidth: true

                ColumnLayout {
                    spacing: 4
                    Text {
                        text: "Статистика"
                        color: PersonalTheme.text
                        font.family: PersonalTheme.displayFont
                        font.pixelSize: 34
                    }
                    Text {
                        text: "Привычки запуска и состояние компьютера"
                        color: PersonalTheme.muted
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: 12
                    }
                }
                Item { Layout.fillWidth: true }
                Rectangle {
                    width: 144
                    height: 34
                    radius: PersonalTheme.radiusSmall
                    color: refreshHover.hovered ? PersonalTheme.surfaceHover : PersonalTheme.surface
                    border.width: 1
                    border.color: PersonalTheme.border
                    Accessible.role: Accessible.Button
                    Accessible.name: "Обновить статистику"
                    Row {
                        anchors.centerIn: parent
                        spacing: 8
                        Text {
                            text: "↻"
                            color: PersonalTheme.accent
                            font.pixelSize: 17
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Text {
                            text: backend.statsUpdatedLabel
                            color: PersonalTheme.muted
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: 10
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                    HoverHandler { id: refreshHover }
                    TapHandler { onTapped: backend.refreshSystemStats() }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                Text {
                    text: "Часто используемые"
                    color: PersonalTheme.text
                    font.family: PersonalTheme.bodyFont
                    font.pixelSize: 17
                    font.weight: Font.DemiBold
                }

                Text {
                    visible: backend.frequentPrograms.length === 0
                    Layout.fillWidth: true
                    Layout.preferredHeight: 88
                    text: "Здесь появятся программы, которые вы запускаете через ассистента.\nПриложения из быстрого запуска не учитываются."
                    color: PersonalTheme.muted
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    font.family: PersonalTheme.bodyFont
                    font.pixelSize: 12
                }

                GridLayout {
                    visible: backend.frequentPrograms.length > 0
                    Layout.fillWidth: true
                    columns: Math.min(5, backend.frequentPrograms.length)
                    columnSpacing: 12

                    Repeater {
                        model: backend.frequentPrograms

                        PersonalPanel {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 184

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 8

                                Rectangle {
                                    width: 38
                                    height: 38
                                    radius: 10
                                    color: PersonalTheme.surfaceRaised
                                    border.width: 1
                                    border.color: PersonalTheme.border
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
                                    Layout.fillWidth: true
                                    text: modelData.name
                                    color: PersonalTheme.text
                                    elide: Text.ElideRight
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: 12
                                    font.weight: Font.DemiBold
                                }
                                Text {
                                    text: modelData.launchLabel
                                    color: PersonalTheme.muted
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: 10
                                }
                                Row {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30
                                    spacing: 3
                                    Repeater {
                                        model: modelData.bars
                                        Rectangle {
                                            required property real modelData
                                            width: 4
                                            height: Math.max(5, 28 * modelData)
                                            radius: 2
                                            color: PersonalTheme.accentMuted
                                            anchors.bottom: parent.bottom
                                        }
                                    }
                                }
                                Item { Layout.fillHeight: true }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30
                                    radius: 7
                                    color: programHover.hovered ? PersonalTheme.accentMuted : PersonalTheme.surfaceHover
                                    border.width: 1
                                    border.color: PersonalTheme.borderStrong
                                    Text {
                                        anchors.centerIn: parent
                                        text: "Запустить"
                                        color: PersonalTheme.text
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: 11
                                    }
                                    HoverHandler { id: programHover }
                                    TapHandler {
                                        enabled: !backend.busy
                                        onTapped: backend.launchProgram(modelData.command)
                                    }
                                }
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
                spacing: 12

                Text {
                    text: "Состояние системы"
                    color: PersonalTheme.text
                    font.family: PersonalTheme.bodyFont
                    font.pixelSize: 17
                    font.weight: Font.DemiBold
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Repeater {
                        model: root.resourceItems()

                        PersonalPanel {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 118

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 8

                                RowLayout {
                                    Layout.fillWidth: true
                                    Text {
                                        text: modelData.label
                                        color: PersonalTheme.muted
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: 11
                                    }
                                    Item { Layout.fillWidth: true }
                                    Text {
                                        text: modelData.available === false ? "—" : modelData.percent + "%"
                                        color: PersonalTheme.text
                                        font.family: PersonalTheme.utilityFont
                                        font.pixelSize: 24
                                    }
                                }
                                Text {
                                    text: modelData.detail
                                    color: PersonalTheme.subtle
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: 10
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 5
                                    radius: 3
                                    color: PersonalTheme.backgroundDeep
                                    Rectangle {
                                        width: parent.width * Math.max(0, Math.min(100, modelData.percent)) / 100
                                        height: parent.height
                                        radius: parent.radius
                                        color: PersonalTheme.accent
                                    }
                                }
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 10

                Text {
                    text: "Диски"
                    color: PersonalTheme.text
                    font.family: PersonalTheme.bodyFont
                    font.pixelSize: 17
                    font.weight: Font.DemiBold
                }

                Text {
                    visible: backend.diskItems.length === 0
                    Layout.fillWidth: true
                    Layout.preferredHeight: 54
                    text: "Данные о дисках появятся после обновления."
                    color: PersonalTheme.muted
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    font.family: PersonalTheme.bodyFont
                    font.pixelSize: 11
                }

                Repeater {
                    model: backend.diskItems

                    PersonalPanel {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 56

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 16
                            anchors.rightMargin: 16
                            spacing: 14

                            Text {
                                text: "▱"
                                color: PersonalTheme.accent
                                font.pixelSize: 20
                            }
                            Text {
                                text: modelData.name
                                color: PersonalTheme.text
                                font.family: PersonalTheme.utilityFont
                                font.pixelSize: 12
                                Layout.preferredWidth: 54
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 6
                                radius: 3
                                color: PersonalTheme.backgroundDeep
                                Rectangle {
                                    width: parent.width * Math.max(0, Math.min(100, modelData.percent)) / 100
                                    height: parent.height
                                    radius: parent.radius
                                    color: PersonalTheme.accent
                                }
                            }
                            Text {
                                text: modelData.detail
                                color: PersonalTheme.muted
                                horizontalAlignment: Text.AlignRight
                                font.family: PersonalTheme.utilityFont
                                font.pixelSize: 10
                                Layout.preferredWidth: 150
                            }
                            Text {
                                text: modelData.percent + "%"
                                color: PersonalTheme.text
                                horizontalAlignment: Text.AlignRight
                                font.family: PersonalTheme.utilityFont
                                font.pixelSize: 10
                                Layout.preferredWidth: 38
                            }
                        }
                    }
                }
            }
        }
    }
}
