import QtQuick
import "."

Canvas {
    id: root

    property string name: ""
    property color color: PersonalTheme.muted
    property real strokeWidth: 1.7

    implicitWidth: 24
    implicitHeight: 24
    antialiasing: true

    onNameChanged: requestPaint()
    onColorChanged: requestPaint()
    onStrokeWidthChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    Component.onCompleted: requestPaint()

    onPaint: {
        const c = getContext("2d")
        c.reset()
        c.scale(width / 24, height / 24)
        c.strokeStyle = color
        c.lineWidth = strokeWidth
        c.lineCap = "round"
        c.lineJoin = "round"
        c.beginPath()

        if (name === "home") {
            c.moveTo(3.5, 11); c.lineTo(12, 4); c.lineTo(20.5, 11)
            c.moveTo(5.8, 9.8); c.lineTo(5.8, 20); c.lineTo(18.2, 20); c.lineTo(18.2, 9.8)
            c.moveTo(9.5, 20); c.lineTo(9.5, 14); c.lineTo(14.5, 14); c.lineTo(14.5, 20)
        } else if (name === "statistics") {
            c.moveTo(4, 20); c.lineTo(20, 20)
            c.moveTo(6, 17); c.lineTo(6, 12); c.lineTo(9, 12); c.lineTo(9, 17)
            c.moveTo(11, 17); c.lineTo(11, 8); c.lineTo(14, 8); c.lineTo(14, 17)
            c.moveTo(16, 17); c.lineTo(16, 4); c.lineTo(19, 4); c.lineTo(19, 17)
        } else if (name === "customization") {
            c.arc(9, 9, 4.7, 0, Math.PI * 2)
            c.moveTo(12.5, 12.5); c.lineTo(19.5, 19.5)
            c.moveTo(6.8, 9); c.lineTo(11.2, 9)
            c.moveTo(9, 6.8); c.lineTo(9, 11.2)
        } else if (name === "settings") {
            c.moveTo(4, 6); c.lineTo(20, 6)
            c.moveTo(4, 12); c.lineTo(20, 12)
            c.moveTo(4, 18); c.lineTo(20, 18)
            c.moveTo(8, 3.5); c.lineTo(8, 8.5)
            c.moveTo(16, 9.5); c.lineTo(16, 14.5)
            c.moveTo(10, 15.5); c.lineTo(10, 20.5)
        } else if (name === "send") {
            c.moveTo(4, 5); c.lineTo(21, 12); c.lineTo(4, 19); c.lineTo(7, 12); c.lineTo(21, 12)
        } else if (name === "game") {
            c.moveTo(7.5, 8); c.bezierCurveTo(4.5, 8, 3, 11.5, 3, 16)
            c.bezierCurveTo(3, 19, 5.2, 20, 7, 17); c.lineTo(9, 15); c.lineTo(15, 15)
            c.lineTo(17, 17); c.bezierCurveTo(18.8, 20, 21, 19, 21, 16)
            c.bezierCurveTo(21, 11.5, 19.5, 8, 16.5, 8); c.closePath()
            c.moveTo(7, 11.5); c.lineTo(11, 11.5); c.moveTo(9, 9.5); c.lineTo(9, 13.5)
            c.moveTo(16.5, 11); c.lineTo(16.5, 11.1); c.moveTo(18.5, 13); c.lineTo(18.5, 13.1)
        } else if (name === "shield") {
            c.moveTo(12, 3); c.lineTo(20, 6); c.lineTo(20, 11.5)
            c.bezierCurveTo(20, 16.5, 16.8, 19.5, 12, 21); c.bezierCurveTo(7.2, 19.5, 4, 16.5, 4, 11.5)
            c.lineTo(4, 6); c.closePath(); c.moveTo(8.5, 12); c.lineTo(11, 14.5); c.lineTo(16, 9.5)
        } else if (name === "terminal") {
            c.rect(3, 4, 18, 16); c.moveTo(7, 9); c.lineTo(10, 12); c.lineTo(7, 15)
            c.moveTo(12.5, 15); c.lineTo(17, 15)
        } else if (name === "chevron-right") {
            c.moveTo(9, 5); c.lineTo(16, 12); c.lineTo(9, 19)
        } else if (name === "minimize") {
            c.moveTo(5, 12); c.lineTo(19, 12)
        } else if (name === "maximize") {
            c.rect(5, 5, 14, 14)
        } else if (name === "close") {
            c.moveTo(6, 6); c.lineTo(18, 18); c.moveTo(18, 6); c.lineTo(6, 18)
        }

        c.stroke()
    }
}
