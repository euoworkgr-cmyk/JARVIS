import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: root

    function submitCommand() {
        const command = commandField.text.trim()
        if (command.length === 0 || backend.busy)
            return
        backend.executeCommand(command)
        commandField.text = ""
    }

    function historyTime(value) {
        const date = new Date(value)
        return isNaN(date.getTime()) ? "" : Qt.formatTime(date, "HH:mm")
    }

    function historyStatusLabel(status) {
        if (status === "success")
            return "Готово"
        if (status === "error" || status === "not_found")
            return "Ошибка"
        if (status === "pending")
            return "Ожидание"
        return "Выполнено"
    }

    Flickable {
        id: pageFlickable
        anchors.fill: parent
        contentWidth: content.width
        contentHeight: content.implicitHeight + 12
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: PersonalScrollBar { policy: ScrollBar.AsNeeded }

        Item {
            id: content
            width: Math.max(0, pageFlickable.width - 14)
            implicitHeight: pageColumn.implicitHeight

            ColumnLayout {
                id: pageColumn
                width: parent.width
                spacing: 18

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 218

                    MountainBackdrop {
                        width: parent.width * 0.74
                        height: parent.height
                        anchors.right: parent.right
                        anchors.top: parent.top
                    }

                    Column {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.topMargin: 12
                        width: Math.min(620, parent.width * 0.72)
                        spacing: 14

                        Text {
                            width: parent.width
                            text: "Привет, " + backend.displayName + "!\nКак я могу помочь?"
                            color: PersonalTheme.text
                            font.family: PersonalTheme.displayFont
                            font.pixelSize: 38
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
                                    model: [8, 15, 22, 12, 18, 9]
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
                                text: backend.jarvisState === "idle" ? "Готов к команде" : backend.stateLabel
                                color: backend.jarvisState === "error" ? PersonalTheme.danger : PersonalTheme.accent
                                font.family: PersonalTheme.bodyFont
                                font.pixelSize: 12
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }

                        RowLayout {
                            width: parent.width
                            spacing: 8

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 44
                                radius: PersonalTheme.radiusSmall
                                color: PersonalTheme.surface
                                border.width: commandField.activeFocus ? 1.5 : 1
                                border.color: commandField.activeFocus ? PersonalTheme.accent
                                                                      : PersonalTheme.border

                                TextField {
                                    id: commandField
                                    anchors.fill: parent
                                    leftPadding: 14
                                    rightPadding: 64
                                    enabled: !backend.busy
                                    color: PersonalTheme.text
                                    selectionColor: PersonalTheme.accentMuted
                                    selectedTextColor: PersonalTheme.text
                                    placeholderText: "Введите команду"
                                    placeholderTextColor: PersonalTheme.subtle
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: 12
                                    Accessible.name: "Команда JARVIS"
                                    background: Item { }
                                    onAccepted: root.submitCommand()
                                }

                                Text {
                                    anchors.right: parent.right
                                    anchors.rightMargin: 12
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: "Ctrl+K"
                                    color: PersonalTheme.subtle
                                    font.family: PersonalTheme.utilityFont
                                    font.pixelSize: 8
                                }
                            }

                            Control {
                                id: executeControl
                                Layout.preferredWidth: 88
                                Layout.preferredHeight: 44
                                enabled: !backend.busy
                                activeFocusOnTab: true
                                opacity: enabled ? 1 : 0.58
                                Accessible.role: Accessible.Button
                                Accessible.name: "Выполнить команду"

                                background: Rectangle {
                                    radius: PersonalTheme.radiusSmall
                                    color: executeTap.pressed || executeHover.hovered
                                           ? PersonalTheme.accentBright : PersonalTheme.accent
                                    border.width: executeControl.activeFocus ? 2 : 0
                                    border.color: PersonalTheme.text

                                    Behavior on color {
                                        ColorAnimation { duration: PersonalTheme.motionFast }
                                    }
                                }

                                contentItem: Text {
                                    text: backend.busy ? "Выполняю" : "Запустить"
                                    color: "#17190F"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                }

                                HoverHandler { id: executeHover }
                                TapHandler {
                                    id: executeTap
                                    enabled: executeControl.enabled
                                    onTapped: commandField.text.trim().length > 0
                                              ? root.submitCommand()
                                              : commandField.forceActiveFocus()
                                }
                                Keys.onPressed: function(event) {
                                    if (event.key === Qt.Key_Return || event.key === Qt.Key_Space) {
                                        if (commandField.text.trim().length > 0)
                                            root.submitCommand()
                                        else
                                            commandField.forceActiveFocus()
                                        event.accepted = true
                                    }
                                }
                            }
                        }
                    }

                    Shortcut {
                        sequence: "Ctrl+K"
                        onActivated: commandField.forceActiveFocus()
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        text: "Быстрый запуск"
                        color: PersonalTheme.text
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: 17
                        font.weight: Font.Medium
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 5
                        columnSpacing: 10

                        Repeater {
                            model: backend.presetItems

                            Control {
                                id: presetCard
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.minimumWidth: 0
                                Layout.preferredWidth: 1
                                Layout.preferredHeight: 98
                                enabled: !backend.busy
                                activeFocusOnTab: true
                                opacity: enabled ? 1 : 0.58
                                Accessible.role: Accessible.Button
                                Accessible.name: "Запустить " + modelData.title

                                transform: Translate {
                                    y: presetHover.hovered ? -1 : 0
                                    Behavior on y {
                                        enabled: !backend.reducedMotion
                                        NumberAnimation {
                                            duration: PersonalTheme.motionFast
                                            easing.type: Easing.OutCubic
                                        }
                                    }
                                }

                                background: Rectangle {
                                    radius: PersonalTheme.radiusMedium
                                    color: presetTap.pressed ? PersonalTheme.backgroundDeep
                                                             : presetHover.hovered ? PersonalTheme.surfaceHover
                                                                                   : PersonalTheme.surface
                                    border.width: presetCard.activeFocus ? 1.5 : 1
                                    border.color: presetCard.activeFocus ? PersonalTheme.accent
                                                                         : presetHover.hovered ? PersonalTheme.borderStrong
                                                                                               : PersonalTheme.border

                                    Behavior on color {
                                        ColorAnimation { duration: PersonalTheme.motionFast }
                                    }
                                }

                                contentItem: ColumnLayout {
                                    spacing: 7

                                    Item {
                                        Layout.topMargin: 11
                                        Layout.alignment: Qt.AlignHCenter
                                        Layout.preferredWidth: 42
                                        Layout.preferredHeight: 42

                                        Image {
                                            id: appIcon
                                            anchors.centerIn: parent
                                            width: 40
                                            height: 40
                                            source: "image://programicons/" + presetCard.modelData.number
                                            sourceSize: Qt.size(40, 40)
                                            fillMode: Image.PreserveAspectFit
                                            smooth: true
                                            cache: true
                                        }

                                        Rectangle {
                                            anchors.fill: parent
                                            visible: appIcon.status !== Image.Ready
                                            radius: PersonalTheme.radiusSmall
                                            color: PersonalTheme.accentGhost
                                            border.width: 1
                                            border.color: PersonalTheme.accentMuted

                                            Text {
                                                anchors.centerIn: parent
                                                text: presetCard.modelData.monogram
                                                color: PersonalTheme.accent
                                                font.family: PersonalTheme.utilityFont
                                                font.pixelSize: 10
                                                font.weight: Font.DemiBold
                                            }
                                        }
                                    }

                                    Text {
                                        Layout.fillWidth: true
                                        Layout.leftMargin: 8
                                        Layout.rightMargin: 8
                                        text: presetCard.modelData.title
                                        color: PersonalTheme.text
                                        wrapMode: Text.WordWrap
                                        maximumLineCount: 2
                                        horizontalAlignment: Text.AlignHCenter
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: 11
                                    }
                                }

                                HoverHandler { id: presetHover }
                                TapHandler {
                                    id: presetTap
                                    enabled: presetCard.enabled
                                    onTapped: backend.launchPreset(presetCard.modelData.number)
                                }
                                Keys.onPressed: function(event) {
                                    if (event.key === Qt.Key_Return || event.key === Qt.Key_Space) {
                                        backend.launchPreset(presetCard.modelData.number)
                                        event.accepted = true
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
                    spacing: 10

                    Text {
                        text: "Протоколы"
                        color: PersonalTheme.text
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: 17
                        font.weight: Font.Medium
                    }

                    Repeater {
                        model: backend.protocolItems

                        Control {
                            id: protocolRow
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 58
                            enabled: !backend.busy
                            activeFocusOnTab: true
                            opacity: enabled ? 1 : 0.58
                            Accessible.role: Accessible.Button
                            Accessible.name: "Запустить протокол " + modelData.title

                            transform: Translate {
                                y: protocolHover.hovered ? -1 : 0
                                Behavior on y {
                                    enabled: !backend.reducedMotion
                                    NumberAnimation {
                                        duration: PersonalTheme.motionFast
                                        easing.type: Easing.OutCubic
                                    }
                                }
                            }

                            background: Rectangle {
                                radius: PersonalTheme.radiusSmall
                                color: protocolTap.pressed ? PersonalTheme.backgroundDeep
                                                           : protocolHover.hovered ? PersonalTheme.surfaceHover
                                                                                   : PersonalTheme.surface
                                border.width: protocolRow.activeFocus ? 1.5 : 1
                                border.color: protocolRow.activeFocus ? PersonalTheme.accent
                                                                      : protocolHover.hovered ? PersonalTheme.borderStrong
                                                                                              : PersonalTheme.border

                                Behavior on color {
                                    ColorAnimation { duration: PersonalTheme.motionFast }
                                }
                            }

                            contentItem: RowLayout {
                                spacing: 13

                                Text {
                                    Layout.leftMargin: 16
                                    Layout.preferredWidth: 28
                                    text: protocolRow.modelData.symbol
                                    color: PersonalTheme.accent
                                    horizontalAlignment: Text.AlignHCenter
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: 20
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    Text {
                                        text: protocolRow.modelData.title
                                        color: PersonalTheme.text
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: 13
                                        font.weight: Font.Medium
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: protocolRow.modelData.detail
                                        color: PersonalTheme.muted
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: 10
                                    }
                                }

                                Rectangle {
                                    visible: protocolRow.modelData.extra
                                    Layout.preferredWidth: 40
                                    Layout.preferredHeight: 19
                                    radius: 4
                                    color: "transparent"
                                    border.width: 1
                                    border.color: PersonalTheme.warning
                                    Text {
                                        anchors.centerIn: parent
                                        text: "Extra"
                                        color: PersonalTheme.warning
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: 8
                                    }
                                }

                                Text {
                                    Layout.rightMargin: 16
                                    text: "›"
                                    color: protocolHover.hovered ? PersonalTheme.text : PersonalTheme.muted
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: 24
                                }
                            }

                            HoverHandler { id: protocolHover }
                            TapHandler {
                                id: protocolTap
                                enabled: protocolRow.enabled
                                onTapped: backend.runProtocol(protocolRow.modelData.id)
                            }
                            Keys.onPressed: function(event) {
                                if (event.key === Qt.Key_Return || event.key === Qt.Key_Space) {
                                    backend.runProtocol(protocolRow.modelData.id)
                                    event.accepted = true
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
                            text: "Последние команды"
                            color: PersonalTheme.text
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: 17
                            font.weight: Font.Medium
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            Layout.rightMargin: 8
                            text: backend.historyItems.length + " из 100"
                            color: PersonalTheme.subtle
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: 10
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 202
                        radius: PersonalTheme.radiusMedium
                        color: PersonalTheme.surface
                        border.width: 1
                        border.color: PersonalTheme.border

                        Column {
                            visible: backend.historyItems.length === 0
                            anchors.centerIn: parent
                            spacing: 5
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "История пока пуста"
                                color: PersonalTheme.text
                                font.family: PersonalTheme.bodyFont
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "Выполненные команды появятся здесь."
                                color: PersonalTheme.muted
                                font.family: PersonalTheme.bodyFont
                                font.pixelSize: 10
                            }
                        }

                        ListView {
                            id: historyList
                            anchors.fill: parent
                            anchors.margins: 8
                            visible: count > 0
                            model: backend.historyItems
                            spacing: 4
                            clip: true
                            boundsBehavior: Flickable.StopAtBounds
                            ScrollBar.vertical: PersonalScrollBar { policy: ScrollBar.AsNeeded }
                            onCountChanged: Qt.callLater(positionViewAtEnd)

                            delegate: Rectangle {
                                id: historyRow
                                required property var modelData
                                width: historyList.width - 14
                                height: 28
                                radius: 6
                                color: PersonalTheme.surfaceRaised
                                border.width: 1
                                border.color: PersonalTheme.border

                                readonly property color statusColor: modelData.status === "success" ? PersonalTheme.success
                                                                           : modelData.status === "error" || modelData.status === "not_found" ? PersonalTheme.danger
                                                                           : modelData.status === "pending" ? PersonalTheme.warning
                                                                           : PersonalTheme.muted

                                Rectangle {
                                    width: 2
                                    height: 16
                                    radius: 1
                                    color: historyRow.statusColor
                                    anchors.left: parent.left
                                    anchors.leftMargin: 8
                                    anchors.verticalCenter: parent.verticalCenter
                                }

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 18
                                    anchors.rightMargin: 10
                                    spacing: 10

                                    Text {
                                        Layout.preferredWidth: 210
                                        text: historyRow.modelData.command
                                        color: PersonalTheme.text
                                        fontSizeMode: Text.HorizontalFit
                                        minimumPixelSize: 7
                                        font.family: PersonalTheme.utilityFont
                                        font.pixelSize: 10
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: historyRow.modelData.title
                                        color: PersonalTheme.muted
                                        fontSizeMode: Text.HorizontalFit
                                        minimumPixelSize: 8
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: 10
                                    }
                                    Text {
                                        text: root.historyStatusLabel(historyRow.modelData.status)
                                        color: historyRow.statusColor
                                        font.family: PersonalTheme.bodyFont
                                        font.pixelSize: 9
                                    }
                                    Text {
                                        Layout.preferredWidth: 34
                                        text: root.historyTime(historyRow.modelData.timestamp)
                                        color: PersonalTheme.subtle
                                        horizontalAlignment: Text.AlignRight
                                        font.family: PersonalTheme.utilityFont
                                        font.pixelSize: 9
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
