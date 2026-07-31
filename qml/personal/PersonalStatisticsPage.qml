import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import ".." as Shared

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
            width: Math.round(Math.max(0, pageFlickable.width - 14))
            spacing: 18

            Shared.LabelSmooth {
                text: "Часто используемые"
                color: PersonalTheme.text
                font.family: PersonalTheme.bodyFont
                font.pixelSize: PersonalTheme.title
                font.weight: Font.Medium
            }

            PersonalPanel {
                visible: backend.frequentPrograms.length === 0
                Layout.fillWidth: true
                Layout.preferredHeight: 86

                Shared.LabelSharp {
                    anchors.fill: parent
                    anchors.margins: 18
                    text: "Здесь появятся программы, которые вы запускаете через ассистента.\nПриложения из быстрого запуска не учитываются."
                    color: PersonalTheme.muted
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    font.family: PersonalTheme.bodyFont
                    font.pixelSize: PersonalTheme.caption
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

                                Image {
                                    id: frequentProgramIcon
                                    anchors.centerIn: parent
                                    width: 32
                                    height: 32
                                    source: "image://programicons/program/" + modelData.iconId
                                    sourceSize: Qt.size(32, 32)
                                    fillMode: Image.PreserveAspectFit
                                    smooth: true
                                    cache: false
                                }

                                Shared.LabelSharp {
                                    anchors.centerIn: parent
                                    visible: frequentProgramIcon.status !== Image.Ready
                                    text: modelData.monogram
                                    color: PersonalTheme.accent
                                    font.family: PersonalTheme.utilityFont
                                    font.pixelSize: PersonalTheme.micro
                                    font.weight: Font.DemiBold
                                }
                            }

                            Shared.LabelSharp {
                                Layout.fillWidth: true
                                text: modelData.name
                                color: PersonalTheme.text
                                elide: Text.ElideRight
                                font.family: PersonalTheme.bodyFont
                                font.pixelSize: PersonalTheme.label
                                font.weight: Font.DemiBold
                            }

                            Shared.LabelSharp {
                                text: modelData.launchLabel
                                color: PersonalTheme.muted
                                font.family: PersonalTheme.bodyFont
                                font.pixelSize: PersonalTheme.micro
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
                                        height: Math.round(Math.max(5, 28 * modelData))
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

                                Shared.LabelSharp {
                                    anchors.centerIn: parent
                                    text: "Запустить"
                                    color: PersonalTheme.text
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: PersonalTheme.caption
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

            Shared.LabelSmooth {
                text: "Состояние системы"
                color: PersonalTheme.text
                font.family: PersonalTheme.bodyFont
                font.pixelSize: PersonalTheme.title
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

                                    Shared.LabelSharp {
                                        text: modelData.label
                                        color: PersonalTheme.text
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: PersonalTheme.body
                                        font.weight: Font.Medium
                                    }

                                    Shared.LabelSmooth {
                                        text: modelData.available === false ? "—" : modelData.percent + "%"
                                        color: PersonalTheme.text
                                        font.family: PersonalTheme.utilityFont
                                        font.pixelSize: PersonalTheme.hero
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
                                            const x = Math.round(point * width / 13)
                                            const phase = value * 0.07 + point * 1.7
                                            const pulse = Math.sin(phase) * 4 + Math.cos(phase * 0.61) * 3
                                            const y = Math.round(height * 0.54 - pulse)
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
                                    id: resourceProgress
                                    property bool revealed: false
                                    width: Math.round(parent.width * Math.max(0, Math.min(100, modelData.percent)) / 100)
                                    height: parent.height
                                    radius: parent.radius
                                    color: PersonalTheme.accent
                                    transformOrigin: Item.Left
                                    scale: revealed ? 1 : 0

                                    Behavior on scale {
                                        NumberAnimation {
                                            duration: PersonalTheme.durProgress
                                            easing.type: PersonalTheme.easeOut
                                        }
                                    }
                                    Component.onCompleted: Qt.callLater(function() { revealed = true })
                                }
                            }
                        }
                    }
                }
            }

            Shared.LabelSmooth {
                text: "Диски"
                color: PersonalTheme.text
                font.family: PersonalTheme.bodyFont
                font.pixelSize: PersonalTheme.title
                font.weight: Font.Medium
            }

            Shared.LabelSharp {
                visible: backend.diskItems.length === 0
                Layout.fillWidth: true
                Layout.preferredHeight: 54
                text: "Данные о дисках появятся после обновления."
                color: PersonalTheme.muted
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.family: PersonalTheme.bodyFont
                font.pixelSize: PersonalTheme.caption
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

                        Shared.LabelSmooth {
                            text: "▱"
                            color: PersonalTheme.accent
                            font.pixelSize: PersonalTheme.title
                        }

                        Shared.LabelSharp {
                            text: modelData.name
                            color: PersonalTheme.text
                            font.family: PersonalTheme.utilityFont
                            font.pixelSize: PersonalTheme.label
                            Layout.preferredWidth: 44
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 6
                            radius: 3
                            color: PersonalTheme.backgroundDeep

                            Rectangle {
                                id: diskProgress
                                property bool revealed: false
                                width: Math.round(parent.width * Math.max(0, Math.min(100, modelData.percent)) / 100)
                                height: parent.height
                                radius: parent.radius
                                color: PersonalTheme.accent
                                transformOrigin: Item.Left
                                scale: revealed ? 1 : 0

                                Behavior on scale {
                                    NumberAnimation {
                                        duration: PersonalTheme.durProgress
                                        easing.type: PersonalTheme.easeOut
                                    }
                                }
                                Component.onCompleted: Qt.callLater(function() { revealed = true })
                            }
                        }

                        Shared.LabelSharp {
                            text: modelData.detail
                            color: PersonalTheme.muted
                            horizontalAlignment: Text.AlignRight
                            font.family: PersonalTheme.utilityFont
                            font.pixelSize: PersonalTheme.micro
                            Layout.preferredWidth: 148
                        }

                        Shared.LabelSharp {
                            text: modelData.percent + "%"
                            color: PersonalTheme.text
                            horizontalAlignment: Text.AlignRight
                            font.family: PersonalTheme.utilityFont
                            font.pixelSize: PersonalTheme.micro
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

                    Shared.LabelSmooth {
                        text: "↻"
                        color: refreshHover.hovered ? PersonalTheme.accentBright : PersonalTheme.accent
                        font.pixelSize: PersonalTheme.title
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Shared.LabelSharp {
                        text: backend.statsUpdatedLabel
                        color: refreshHover.hovered ? PersonalTheme.text : PersonalTheme.muted
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: PersonalTheme.micro
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                HoverHandler { id: refreshHover }
                TapHandler { onTapped: backend.refreshSystemStats() }
            }
        }
    }
}
