import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import ".." as Shared

Item {
    id: root

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
    }
}
