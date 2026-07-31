import QtQuick
import QtQuick.Layouts
import "."
import ".." as Shared

Item {
    ColumnLayout {
        anchors.fill: parent
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

        Item { Layout.fillHeight: true }
    }
}
