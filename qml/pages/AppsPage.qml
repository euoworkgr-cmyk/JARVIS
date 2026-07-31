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
            Column {
                spacing: 3
                LabelSmooth {
                    text: "ПРИЛОЖЕНИЯ"
                    color: Theme.text
                    font.family: Theme.headingFont
                    font.pixelSize: Theme.hero
                    font.weight: Font.DemiBold
                    font.letterSpacing: 0.8
                }
                LabelSharp {
                    text: backend.programItems.length + " программ в локальном индексе Windows"
                    color: Theme.muted
                    font.family: Theme.bodyFont
                    font.pixelSize: Theme.body
                }
            }
            Item { Layout.fillWidth: true }
            ActionButton {
                text: backend.busy ? "Обновляю…" : "Обновить индекс"
                enabled: !backend.busy
                onClicked: backend.refreshPrograms()
            }
        }

        GlassPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 142

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 12
                LabelSharp {
                    text: "БЫСТРЫЙ ЗАПУСК"
                    color: Theme.muted
                    font.family: Theme.monoFont
                    font.pixelSize: Theme.micro
                    font.letterSpacing: 1.2
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 9
                    Repeater {
                        model: [
                            ["1", "Яндекс"],
                            ["2", "ChatGPT"],
                            ["3", "VS Code"],
                            ["4", "Telegram"],
                            ["5", "Камера"]
                        ]
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 70
                            radius: 14
                            color: presetHover.hovered ? "#D01A3D78" : "#B30E234C"
                            border.width: 1
                            border.color: presetHover.hovered ? Theme.borderStrong : Theme.border
                            Accessible.role: Accessible.Button
                            Accessible.name: "Открыть " + modelData[1]

                            Row {
                                anchors.centerIn: parent
                                spacing: 10
                                Rectangle {
                                    width: 30
                                    height: 30
                                    radius: 10
                                    color: "#2E68A7FF"
                                    LabelSharp {
                                        anchors.centerIn: parent
                                        text: modelData[0]
                                        color: Theme.accent
                                        font.family: Theme.monoFont
                                        font.pixelSize: Theme.label
                                        font.weight: Font.Bold
                                    }
                                }
                                LabelSharp {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: modelData[1]
                                    color: Theme.text
                                    font.family: Theme.bodyFont
                                    font.pixelSize: Theme.body
                                    font.weight: Font.DemiBold
                                }
                            }
                            HoverHandler { id: presetHover }
                            TapHandler { onTapped: backend.executeCommand(modelData[0]) }
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 14

            GlassPanel {
                Layout.fillWidth: true
                Layout.fillHeight: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 12

                    RowLayout {
                        Layout.fillWidth: true
                        TextField {
                            id: searchField
                            Layout.fillWidth: true
                            Layout.preferredHeight: 44
                            leftPadding: 16
                            rightPadding: 16
                            color: Theme.text
                            placeholderText: "Найти приложение…"
                            placeholderTextColor: "#7388B2"
                            font.family: Theme.bodyFont
                            font.pixelSize: Theme.title
                            renderType: Text.QtRendering
                            Accessible.name: "Поиск приложений"
                            background: Rectangle {
                                radius: 12
                                color: "#B4081734"
                                border.width: searchField.activeFocus ? 2 : 1
                                border.color: searchField.activeFocus ? Theme.accent : Theme.border

                                Behavior on border.width {
                                    NumberAnimation { duration: Theme.durFocus; easing.type: Theme.easeOut }
                                }
                                Behavior on border.color {
                                    ColorAnimation { duration: Theme.durFocus }
                                }
                            }
                        }
                    }

                    ListView {
                        id: programList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: backend.programItems
                        spacing: 7
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                        delegate: Rectangle {
                            id: programRow
                            required property var modelData
                            readonly property bool matches: searchField.text.trim().length === 0
                                                             || modelData.name.toLowerCase().indexOf(searchField.text.trim().toLowerCase()) !== -1
                            width: programList.width - 12
                            height: matches ? 48 : 0
                            visible: matches
                            radius: 12
                            color: programHover.hovered ? "#C0163264" : "#8A0C1C3D"
                            border.width: 1
                            border.color: programHover.hovered ? Theme.borderStrong : "#2E5B82BC"
                            Accessible.role: Accessible.Button
                            Accessible.name: "Открыть " + modelData.name

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 14
                                anchors.rightMargin: 12
                                Rectangle {
                                    width: 27
                                    height: 27
                                    radius: 8
                                    color: "#2338A7FF"
                                    LabelSharp {
                                        anchors.centerIn: parent
                                        text: modelData.name.length > 0 ? modelData.name.charAt(0).toUpperCase() : "A"
                                        color: Theme.accent
                                        font.family: Theme.headingFont
                                        font.pixelSize: Theme.label
                                        font.weight: Font.Bold
                                    }
                                }
                                LabelSharp {
                                    Layout.fillWidth: true
                                    text: modelData.name
                                    color: Theme.text
                                    elide: Text.ElideRight
                                    font.family: Theme.bodyFont
                                    font.pixelSize: Theme.body
                                }
                                LabelSharp {
                                    text: "Открыть  →"
                                    color: programHover.hovered ? Theme.accent : Theme.muted
                                    font.family: Theme.bodyFont
                                    font.pixelSize: Theme.caption
                                }
                            }
                            HoverHandler { id: programHover }
                            TapHandler { onTapped: backend.launchProgram(modelData.name) }
                        }
                    }
                }
            }

            GlassPanel {
                Layout.preferredWidth: 250
                Layout.fillHeight: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 12
                    LabelSharp {
                        text: "ПЕРСОНАЛЬНЫЕ"
                        color: Theme.muted
                        font.family: Theme.monoFont
                        font.pixelSize: Theme.micro
                        font.letterSpacing: 1.2
                    }

                    Repeater {
                        model: [
                            ["VPN", "Happ Terminal VPN", "Защищённое подключение"],
                            ["Claude code", "Claude Code", "Рабочий ярлык"]
                        ]
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 76
                            radius: 14
                            color: specialHover.hovered ? "#C0163264" : "#9A0D2046"
                            border.width: 1
                            border.color: specialHover.hovered ? Theme.borderStrong : Theme.border
                            Accessible.role: Accessible.Button
                            Accessible.name: "Открыть " + modelData[1]

                            Column {
                                anchors.left: parent.left
                                anchors.leftMargin: 15
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: 4
                                LabelSmooth {
                                    text: modelData[1]
                                    color: Theme.text
                                    font.family: Theme.bodyFont
                                    font.pixelSize: Theme.title
                                    font.weight: Font.DemiBold
                                }
                                LabelSharp {
                                    text: modelData[2]
                                    color: Theme.muted
                                    font.family: Theme.bodyFont
                                    font.pixelSize: Theme.caption
                                }
                            }
                            HoverHandler { id: specialHover }
                            TapHandler { onTapped: backend.executeCommand(modelData[0]) }
                        }
                    }
                    Item { Layout.fillHeight: true }
                    LabelSharp {
                        Layout.fillWidth: true
                        text: "Пути пока используются из текущей конфигурации Supersonic."
                        color: "#657AA4"
                        wrapMode: Text.WordWrap
                        font.family: Theme.bodyFont
                        font.pixelSize: Theme.caption
                    }
                }
            }
        }
    }
}
