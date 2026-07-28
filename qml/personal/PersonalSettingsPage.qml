import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import ".." as Shared

Item {
    id: root

    Connections {
        target: backend
        function onPreferencesChanged() {
            autostartSwitch.checked = backend.autostartEnabled
            voiceStartupSwitch.checked = backend.voiceStartupEnabled
        }
    }

    ColumnLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: 18

        Shared.LabelSmooth {
            text: "Настройки"
            color: PersonalTheme.text
            font.family: PersonalTheme.bodyFont
            font.pixelSize: PersonalTheme.title
            font.weight: Font.Medium
        }

        PersonalPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 92

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 18

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3

                    Shared.LabelSharp {
                        text: "Уменьшить движение"
                        color: PersonalTheme.text
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: PersonalTheme.body
                        font.weight: Font.Medium
                    }

                    Shared.LabelSharp {
                        Layout.fillWidth: true
                        text: "Отключает переходы, пульсацию и анимации элементов интерфейса."
                        color: PersonalTheme.muted
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: PersonalTheme.caption
                        wrapMode: Text.WordWrap
                    }
                }

                Switch {
                    id: reducedMotionSwitch
                    Layout.preferredWidth: 52
                    Layout.preferredHeight: 44
                    checked: Shared.Theme.reducedMotion
                    Accessible.name: "Уменьшить движение"
                    onToggled: Shared.Theme.reducedMotion = checked

                    indicator: Rectangle {
                        width: 44
                        height: 24
                        radius: 12
                        anchors.centerIn: parent
                        color: reducedMotionSwitch.checked
                               ? PersonalTheme.accentMuted : PersonalTheme.surfaceHover
                        border.width: 1
                        border.color: reducedMotionSwitch.checked
                                      ? PersonalTheme.accent : PersonalTheme.borderStrong

                        Behavior on color {
                            ColorAnimation { duration: PersonalTheme.durFast }
                        }

                        Rectangle {
                            width: 18
                            height: 18
                            radius: 9
                            x: Math.round(reducedMotionSwitch.checked ? 23 : 3)
                            anchors.verticalCenter: parent.verticalCenter
                            color: reducedMotionSwitch.checked
                                   ? PersonalTheme.backgroundDeep : PersonalTheme.muted

                            Behavior on x {
                                NumberAnimation {
                                    duration: PersonalTheme.durFast
                                    easing.type: PersonalTheme.easeOut
                                }
                            }
                        }
                    }

                    contentItem: Item { }
                }
            }
        }

        PersonalPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 92

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 18

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3

                    Shared.LabelSharp {
                        text: "Запускать Supersonic при входе в Windows"
                        color: PersonalTheme.text
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: PersonalTheme.body
                        font.weight: Font.Medium
                    }
                    Shared.LabelSharp {
                        Layout.fillWidth: true
                        text: "Приложение будет запускаться в фоне только после вашего согласия."
                        color: PersonalTheme.muted
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: PersonalTheme.caption
                        wrapMode: Text.WordWrap
                    }
                }

                Switch {
                    id: autostartSwitch
                    checked: backend.autostartEnabled
                    Accessible.name: "Автозапуск Supersonic"
                    onToggled: backend.setAutostartEnabled(checked)
                }
            }
        }

        PersonalPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 92

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 18

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3

                    Shared.LabelSharp {
                        text: "Запускать голосовое управление автоматически"
                        color: PersonalTheme.text
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: PersonalTheme.body
                        font.weight: Font.Medium
                    }
                    Shared.LabelSharp {
                        Layout.fillWidth: true
                        text: backend.voiceStatusLabel
                        color: PersonalTheme.muted
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: PersonalTheme.caption
                        wrapMode: Text.WordWrap
                    }
                }

                Button {
                    visible: backend.voiceStartupEnabled
                             && (backend.voiceStatus === "error"
                                 || backend.voiceStatus === "disabled")
                    text: "Повторить"
                    Accessible.name: "Повторить запуск голосового управления"
                    onClicked: backend.retryVoiceControl()
                }

                Switch {
                    id: voiceStartupSwitch
                    checked: backend.voiceStartupEnabled
                    Accessible.name: "Автозапуск голосового управления"
                    onToggled: backend.setVoiceStartupEnabled(checked)
                }
            }
        }

        Shared.LabelSharp {
            Layout.fillWidth: true
            visible: backend.preferenceError.length > 0
            text: backend.preferenceError
            color: PersonalTheme.danger
            font.family: PersonalTheme.bodyFont
            font.pixelSize: PersonalTheme.caption
            wrapMode: Text.WordWrap
        }
    }
}
