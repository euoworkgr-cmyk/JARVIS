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
        id: pageFlickable
        anchors.fill: parent
        contentWidth: pageColumn.width
        contentHeight: pageColumn.implicitHeight + 12
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: PersonalScrollBar { policy: ScrollBar.AsNeeded }

        ColumnLayout {
            id: pageColumn
            width: Math.max(0, pageFlickable.width - 14)
            spacing: 18

            Text {
                text: "Часто используемые"
                color: PersonalTheme.text
                font.family: PersonalTheme.bodyFont
                font.pixelSize: 17
                font.weight: Font.Medium
            }

            PersonalPanel {
                visible: backend.frequentPrograms.length === 0
                Layout.fillWidth: true
                Layout.preferredHeight: 86

                Text {
                    anchors.fill: parent
                    anchors.margins: 18
                    text: "Здесь появятся программы, которые вы запускаете через ассистента.\nПриложения из быстрого запуска не учитываются."
                    color: PersonalTheme.muted
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    font.family: PersonalTheme.bodyFont
                    font.pixelSize: 11
                }
            }

            GridLayout {
                visible: backend.frequentPrograms.length > 0
                Layout.fillWidth: true
                columns: Math.min(4, backend.frequentPrograms.length)
                columnSpacing: 12

                Repeater {
                    model: backend.frequentPrograms

                    PersonalPanel {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 184

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 7

                            Rectangle {
                                Layout.preferredWidth: 38
                                Layout.preferredHeight: 38
                                radius: 10
                                color: PersonalTheme.accentGhost
                                border.width: 1
                                border.color: PersonalTheme.accentMuted

                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.monogram
                                    color: PersonalTheme.accent
                                    font.family: PersonalTheme.utilityFont
                                    font.pixelSize: 10
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
                                color: programTap.pressed || programHover.hovered
                                       ? PersonalTheme.accentMuted : PersonalTheme.surfaceHover
                                border.width: 1
                                border.color: PersonalTheme.borderStrong
                                Accessible.role: Accessible.Button
                                Accessible.name: "Запустить " + modelData.name

                                Text {
                                    anchors.centerIn: parent
                                    text: "Запустить"
                                    color: PersonalTheme.text
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: 11
                                }

                                HoverHandler { id: programHover }
                                TapHandler {
                                    id: programTap
                                    enabled: !backend.busy
                                    onTapped: backend.launchProgram(modelData.command)
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

            Text {
                text: "Состояние системы"
                color: PersonalTheme.text
                font.family: PersonalTheme.bodyFont
                font.pixelSize: 17
                font.weight: Font.Medium
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Repeater {
                    model: root.resourceItems()

                    PersonalPanel {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 112

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 7

                            RowLayout {
                                Layout.fillWidth: true

                                ColumnLayout {
                                    spacing: 2

                                    Text {
                                        text: modelData.label
                                        color: PersonalTheme.text
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: 13
                                        font.weight: Font.Medium
                                    }

                                    Text {
                                        text: modelData.available === false ? "—" : modelData.percent + "%"
                                        color: PersonalTheme.text
                                        font.family: PersonalTheme.utilityFont
                                        font.pixelSize: 23
                                    }
                                }

                                Item { Layout.fillWidth: true }

                                Canvas {
                                    Layout.preferredWidth: 92
                                    Layout.preferredHeight: 34
                                    antialiasing: true
                                    property real value: Number(modelData.percent || 0)
                                    onValueChanged: requestPaint()
                                    Component.onCompleted: requestPaint()

                                    onPaint: {
                                        const context = getContext("2d")
                                        context.reset()
                                        context.strokeStyle = PersonalTheme.accentMuted
                                        context.lineWidth = 1.25
                                        context.beginPath()
                                        for (let point = 0; point < 14; point++) {
                                            const x = point * width / 13
                                            const phase = value * 0.07 + point * 1.7
                                            const pulse = Math.sin(phase) * 4 + Math.cos(phase * 0.61) * 3
                                            const y = height * 0.54 - pulse
                                            if (point === 0)
                                                context.moveTo(x, y)
                                            else
                                                context.lineTo(x, y)
                                        }
                                        context.stroke()
                                    }
                                }
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
                        }
                    }
                }
            }

            Text {
                text: "Диски"
                color: PersonalTheme.text
                font.family: PersonalTheme.bodyFont
                font.pixelSize: 17
                font.weight: Font.Medium
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
                        spacing: 12

                        Text {
                            text: "▱"
                            color: PersonalTheme.accent
                            font.pixelSize: 19
                        }

                        Text {
                            text: modelData.name
                            color: PersonalTheme.text
                            font.family: PersonalTheme.utilityFont
                            font.pixelSize: 12
                            Layout.preferredWidth: 44
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
                            Layout.preferredWidth: 148
                        }

                        Text {
                            text: modelData.percent + "%"
                            color: PersonalTheme.text
                            horizontalAlignment: Text.AlignRight
                            font.family: PersonalTheme.utilityFont
                            font.pixelSize: 10
                            Layout.preferredWidth: 34
                        }
                    }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 26
                Accessible.role: Accessible.Button
                Accessible.name: "Обновить статистику"

                Row {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 7

                    Text {
                        text: "↻"
                        color: refreshHover.hovered ? PersonalTheme.accentBright : PersonalTheme.accent
                        font.pixelSize: 16
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: backend.statsUpdatedLabel
                        color: refreshHover.hovered ? PersonalTheme.text : PersonalTheme.muted
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: 10
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                HoverHandler { id: refreshHover }
                TapHandler { onTapped: backend.refreshSystemStats() }
            }
        }
    }
}
