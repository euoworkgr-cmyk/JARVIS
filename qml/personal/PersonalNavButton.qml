import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Button {
    id: root
    required property string iconName
    required property string label
    property bool selected: false

    implicitWidth: 160
    implicitHeight: 56
    hoverEnabled: true
    activeFocusOnTab: true
    padding: 0
    Accessible.name: label

    onSelectedChanged: iconCanvas.requestPaint()
    onHoveredChanged: iconCanvas.requestPaint()

    background: Rectangle {
        radius: PersonalTheme.radiusSmall
        color: root.down ? PersonalTheme.surfaceRaised
                         : root.selected ? PersonalTheme.accentGhost
                         : root.hovered ? PersonalTheme.surface : "transparent"
        border.width: root.activeFocus ? 1 : (root.selected ? 1 : 0)
        border.color: root.activeFocus ? PersonalTheme.accent
                                       : root.selected ? PersonalTheme.borderStrong : "transparent"

        Behavior on color {
            ColorAnimation { duration: PersonalTheme.motionFast }
        }

    }

    contentItem: RowLayout {
        spacing: 11

        Item {
            Layout.leftMargin: 13
            Layout.preferredWidth: 24
            Layout.preferredHeight: 24

            Canvas {
                id: iconCanvas
                anchors.fill: parent
                antialiasing: true
                property color strokeColor: root.selected ? PersonalTheme.text
                                                          : root.hovered ? PersonalTheme.text
                                                                         : PersonalTheme.muted
                onStrokeColorChanged: requestPaint()
                Component.onCompleted: requestPaint()

                onPaint: {
                    const context = getContext("2d")
                    context.reset()
                    context.strokeStyle = strokeColor
                    context.lineWidth = 1.6
                    context.lineCap = "round"
                    context.lineJoin = "round"

                    if (root.iconName === "home") {
                        context.beginPath()
                        context.moveTo(4, 11)
                        context.lineTo(12, 4.5)
                        context.lineTo(20, 11)
                        context.moveTo(6.5, 10)
                        context.lineTo(6.5, 19)
                        context.lineTo(17.5, 19)
                        context.lineTo(17.5, 10)
                        context.stroke()
                    } else if (root.iconName === "statistics") {
                        context.beginPath()
                        context.moveTo(5, 19)
                        context.lineTo(5, 13)
                        context.moveTo(12, 19)
                        context.lineTo(12, 8)
                        context.moveTo(19, 19)
                        context.lineTo(19, 4)
                        context.stroke()
                    } else if (root.iconName === "customization") {
                        context.beginPath()
                        context.arc(12, 12, 7, 0, Math.PI * 2)
                        context.moveTo(12, 5)
                        context.arc(12, 12, 3, -Math.PI / 2, Math.PI * 1.5)
                        context.stroke()
                    } else {
                        context.beginPath()
                        context.moveTo(5, 7)
                        context.lineTo(19, 7)
                        context.moveTo(5, 17)
                        context.lineTo(19, 17)
                        context.moveTo(9, 4)
                        context.lineTo(9, 10)
                        context.moveTo(15, 14)
                        context.lineTo(15, 20)
                        context.stroke()
                    }
                }
            }
        }

        Text {
            text: root.label
            color: root.selected ? PersonalTheme.text : PersonalTheme.muted
            font.family: PersonalTheme.bodyFont
            font.pixelSize: 13
            font.weight: root.selected ? Font.DemiBold : Font.Normal
            Layout.fillWidth: true
            verticalAlignment: Text.AlignVCenter
        }

    }
}
