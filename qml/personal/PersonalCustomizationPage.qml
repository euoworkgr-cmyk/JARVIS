import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import ".." as Shared

Item {
    id: root
    property var draftActions: []
    readonly property var actionTypes: [
        { type: "launch", title: "Открыть программу", needsTarget: true },
        { type: "close", title: "Закрыть программу", needsTarget: true },
        { type: "volume_up", title: "Сделать громче", needsTarget: false },
        { type: "volume_down", title: "Сделать тише", needsTarget: false },
        { type: "volume_mute", title: "Включить / выключить звук", needsTarget: false },
        { type: "show_desktop", title: "Показать рабочий стол", needsTarget: false },
        { type: "lock_pc", title: "Заблокировать ПК", needsTarget: false },
        { type: "sleep", title: "Перевести ПК в спящий режим", needsTarget: false },
        { type: "shutdown", title: "Выключить ПК", needsTarget: false },
        { type: "restart", title: "Перезагрузить ПК", needsTarget: false }
    ]

    function actionTitle(action) {
        for (let index = 0; index < actionTypes.length; ++index) {
            if (actionTypes[index].type === action.type)
                return actionTypes[index].title
        }
        return action.type
    }

    ScrollView {
        id: customizationScroll
        anchors.fill: parent
        contentWidth: availableWidth
        clip: true

        ColumnLayout {
            width: customizationScroll.availableWidth
            spacing: PersonalTheme.spacingLarge

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6
            Shared.LabelSmooth {
                text: "Кастомизация"
                color: PersonalTheme.text
                font.family: PersonalTheme.displayFont
                font.pixelSize: PersonalTheme.hero
            }
            Shared.LabelSharp {
                text: "Выберите оформление интерфейса. Настройка сохранится для следующих запусков."
                color: PersonalTheme.muted
                font.family: PersonalTheme.bodyFont
                font.pixelSize: PersonalTheme.body
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: PersonalTheme.spacingMedium

            Repeater {
                model: [
                    { scheme: "dark", title: "Тёмная олива", description: "Спокойная тёмная палитра", background: "#171916", surface: "#282A24", accent: "#B6BB84" },
                    { scheme: "light", title: "Светлая бумага", description: "Мягкая светлая палитра", background: "#F4F1E8", surface: "#FFFFFF", accent: "#687044" }
                ]

                delegate: PersonalPanel {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 230
                    elevated: PersonalTheme.activeScheme === modelData.scheme
                    border.width: PersonalTheme.activeScheme === modelData.scheme ? 2 : 1
                    border.color: PersonalTheme.activeScheme === modelData.scheme ? PersonalTheme.accent : PersonalTheme.border
                    Accessible.role: Accessible.Button
                    Accessible.name: modelData.title

                    Column {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12

                        Rectangle {
                            width: parent.width
                            height: 112
                            radius: PersonalTheme.radiusSmall
                            color: modelData.background
                            border.width: 1
                            border.color: modelData.accent
                            Rectangle {
                                anchors.centerIn: parent
                                width: Math.round(parent.width * 0.72)
                                height: 58
                                radius: 8
                                color: modelData.surface
                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 12
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 54
                                    height: 7
                                    radius: 4
                                    color: modelData.accent
                                }
                            }
                        }
                        Shared.LabelSmooth {
                            text: modelData.title
                            color: PersonalTheme.text
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: PersonalTheme.title
                            font.weight: Font.DemiBold
                        }
                        Shared.LabelSharp {
                            text: modelData.description
                            color: PersonalTheme.muted
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: PersonalTheme.caption
                        }
                    }

                    HoverHandler { id: themeHover }
                    TapHandler { onTapped: backend.setColorScheme(modelData.scheme) }
                }
            }
        }

            Rectangle { Layout.fillWidth: true; height: 1; color: PersonalTheme.border }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                Shared.LabelSmooth {
                    text: "Настройка протоколов"
                    color: PersonalTheme.text
                    font.family: PersonalTheme.displayFont
                    font.pixelSize: PersonalTheme.title
                }
                Shared.LabelSharp {
                    text: "Одна кодовая фраза запускает цепочку действий. Команда всегда начинается со слова «протокол»."
                    color: PersonalTheme.muted
                    font.family: PersonalTheme.bodyFont
                    font.pixelSize: PersonalTheme.body
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }

            PersonalPanel {
                Layout.fillWidth: true
                Layout.preferredHeight: protocolEditor.implicitHeight + 36
                elevated: true

                ColumnLayout {
                    id: protocolEditor
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 18
                    spacing: 12

                    Shared.LabelSharp {
                        text: "КОДОВАЯ ФРАЗА"
                        color: PersonalTheme.accent
                        font.family: PersonalTheme.utilityFont
                        font.pixelSize: PersonalTheme.micro
                        font.weight: Font.DemiBold
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Rectangle {
                            Layout.preferredWidth: 92
                            Layout.preferredHeight: 42
                            color: PersonalTheme.accentGhost
                            border.color: PersonalTheme.border
                            Shared.LabelSharp {
                                anchors.centerIn: parent
                                text: "протокол"
                                color: PersonalTheme.accent
                                font.family: PersonalTheme.utilityFont
                                font.pixelSize: PersonalTheme.body
                            }
                        }
                        TextField {
                            id: phraseField
                            Layout.fillWidth: true
                            Layout.preferredHeight: 42
                            placeholderText: "например, рабочий режим"
                            color: PersonalTheme.text
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: PersonalTheme.body
                            renderType: Text.NativeRendering
                            background: Rectangle {
                                color: PersonalTheme.surface
                                border.color: phraseField.activeFocus ? PersonalTheme.accent : PersonalTheme.border
                            }
                        }
                    }

                    Shared.LabelSharp {
                        text: "ПОСЛЕДОВАТЕЛЬНОСТЬ ДЕЙСТВИЙ"
                        color: PersonalTheme.accent
                        font.family: PersonalTheme.utilityFont
                        font.pixelSize: PersonalTheme.micro
                        font.weight: Font.DemiBold
                    }
                    Repeater {
                        model: root.draftActions
                        delegate: Rectangle {
                            required property var modelData
                            required property int index
                            Layout.fillWidth: true
                            height: 38
                            radius: PersonalTheme.radiusSmall
                            color: PersonalTheme.surface
                            border.color: PersonalTheme.border
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 8
                                Shared.LabelSharp {
                                    text: (index + 1) + ""
                                    color: PersonalTheme.accent
                                    font.family: PersonalTheme.utilityFont
                                    font.pixelSize: PersonalTheme.caption
                                }
                                Shared.LabelSharp {
                                    Layout.fillWidth: true
                                    text: root.actionTitle(modelData) + (modelData.target ? " · " + modelData.target : "")
                                    color: PersonalTheme.text
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: PersonalTheme.body
                                }
                                Button {
                                    text: "×"
                                    flat: true
                                    onClicked: {
                                        const updated = root.draftActions.slice()
                                        updated.splice(index, 1)
                                        root.draftActions = updated
                                    }
                                }
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        ComboBox {
                            id: actionType
                            Layout.preferredWidth: 225
                            model: root.actionTypes
                            textRole: "title"
                        }
                        TextField {
                            id: actionTarget
                            Layout.fillWidth: true
                            visible: root.actionTypes[actionType.currentIndex].needsTarget
                            placeholderText: actionType.currentIndex === 1 ? "Название закрываемой программы" : "Название программы"
                            color: PersonalTheme.text
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: PersonalTheme.body
                            renderType: Text.NativeRendering
                        }
                        Button {
                            text: "Добавить действие"
                            enabled: !root.actionTypes[actionType.currentIndex].needsTarget || actionTarget.text.trim().length > 0
                            onClicked: {
                                const selected = root.actionTypes[actionType.currentIndex]
                                root.draftActions = root.draftActions.concat([{ type: selected.type, target: actionTarget.text.trim() }])
                                actionTarget.clear()
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Item { Layout.fillWidth: true }
                        Button {
                            text: "Сохранить протокол"
                            enabled: phraseField.text.trim().length > 0 && root.draftActions.length > 0
                            onClicked: {
                                if (backend.saveCustomProtocol(phraseField.text, root.draftActions)) {
                                    phraseField.clear()
                                    root.draftActions = []
                                }
                            }
                        }
                    }
                }
            }

            Shared.LabelSharp {
                visible: backend.customProtocolItems.length === 0
                text: "Сохранённых протоколов пока нет. Создайте первый сценарий выше."
                color: PersonalTheme.muted
                font.family: PersonalTheme.bodyFont
                font.pixelSize: PersonalTheme.body
            }

            Repeater {
                model: backend.customProtocolItems
                delegate: PersonalPanel {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: protocolCard.implicitHeight + 28
                    ColumnLayout {
                        id: protocolCard
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 14
                        RowLayout {
                            Layout.fillWidth: true
                            Shared.LabelSmooth {
                                Layout.fillWidth: true
                                text: modelData.command
                                color: PersonalTheme.text
                                font.family: PersonalTheme.bodyFont
                                font.pixelSize: PersonalTheme.title
                            }
                            Button { text: "Запустить"; onClicked: backend.executeCommand(modelData.command) }
                            Button { text: "Удалить"; onClicked: backend.removeCustomProtocol(modelData.phrase) }
                        }
                        Repeater {
                            model: modelData.actions
                            delegate: Shared.LabelSharp {
                                required property var modelData
                                required property int index
                                text: (index + 1) + ". " + modelData.title + (modelData.target ? " — " + modelData.target : "")
                                color: PersonalTheme.muted
                                font.family: PersonalTheme.bodyFont
                                font.pixelSize: PersonalTheme.caption
                            }
                        }
                    }
                }
            }

            Item { Layout.preferredHeight: 12 }
        }
    }
}
