import QtQuick
import "."

Canvas {
    id: canvas
    opacity: 0.38
    antialiasing: true

    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    Component.onCompleted: requestPaint()

    onPaint: {
        const context = getContext("2d")
        context.reset()
        context.lineWidth = 1
        context.strokeStyle = PersonalTheme.borderStrong

        const originX = width * 0.72
        const originY = height * 0.34
        for (let ring = 0; ring < 9; ring++) {
            context.beginPath()
            const radiusX = 68 + ring * 25
            const radiusY = 34 + ring * 17
            for (let point = 0; point <= 90; point++) {
                const angle = point / 90 * Math.PI * 2
                const ripple = Math.sin(angle * 3 + ring * 0.8) * (5 + ring * 0.7)
                const x = originX + Math.cos(angle) * (radiusX + ripple)
                const y = originY + Math.sin(angle) * (radiusY + ripple * 0.45)
                if (point === 0)
                    context.moveTo(x, y)
                else
                    context.lineTo(x, y)
            }
            context.stroke()
        }

        context.globalAlpha = 0.65
        for (let ridge = 0; ridge < 6; ridge++) {
            context.beginPath()
            context.moveTo(width * 0.48, height * (0.78 + ridge * 0.035))
            context.bezierCurveTo(
                width * 0.64,
                height * (0.58 + ridge * 0.03),
                width * 0.78,
                height * (0.96 - ridge * 0.02),
                width,
                height * (0.62 + ridge * 0.025)
            )
            context.stroke()
        }
    }
}
