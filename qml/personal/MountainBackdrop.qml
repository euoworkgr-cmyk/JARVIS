import QtQuick
import "."

Canvas {
    id: canvas
    opacity: 0.52
    antialiasing: true

    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    Component.onCompleted: requestPaint()

    onPaint: {
        const context = getContext("2d")
        context.reset()
        context.lineWidth = 0.8
        context.strokeStyle = PersonalTheme.borderStrong

        // Layered elevation profiles make a readable mountain landscape rather
        // than the abstract rings used by the previous implementation.
        for (let contour = 0; contour < 12; contour++) {
            context.globalAlpha = 0.12 + contour * 0.012
            context.beginPath()
            for (let point = 0; point <= 120; point++) {
                const t = point / 120
                const x = width * (0.18 + t * 0.86)
                const mainPeak = Math.exp(-Math.pow((t - 0.68) / 0.13, 2))
                const leftPeak = Math.exp(-Math.pow((t - 0.42) / 0.18, 2))
                const ridge = Math.sin(t * 25 + contour * 0.52) * (1.4 + contour * 0.1)
                const base = height * (0.78 + contour * 0.023)
                const y = base - mainPeak * height * (0.54 - contour * 0.018)
                               - leftPeak * height * (0.25 - contour * 0.008) + ridge
                if (point === 0)
                    context.moveTo(x, y)
                else
                    context.lineTo(x, y)
            }
            context.stroke()
        }

        context.globalAlpha = 0.19
        for (let tree = 0; tree < 9; tree++) {
            const x = width * (0.62 + tree * 0.047)
            const baseY = height * (0.78 + (tree % 3) * 0.035)
            const treeHeight = 15 + (tree % 4) * 5
            context.beginPath()
            context.moveTo(x, baseY - treeHeight)
            context.lineTo(x - treeHeight * 0.36, baseY)
            context.moveTo(x, baseY - treeHeight)
            context.lineTo(x + treeHeight * 0.36, baseY)
            context.moveTo(x, baseY - treeHeight * 0.68)
            context.lineTo(x - treeHeight * 0.28, baseY - treeHeight * 0.2)
            context.moveTo(x, baseY - treeHeight * 0.68)
            context.lineTo(x + treeHeight * 0.28, baseY - treeHeight * 0.2)
            context.stroke()
        }
    }
}
