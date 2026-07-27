import QtQuick
import ".."

Item {
    id: root
    property string state: "idle"
    property string stateLabel: "Готов к работе"
    property bool reducedMotion: false
    property real phase: 0

    readonly property color semanticColor: state === "error" ? Theme.danger
                                                 : state === "success" ? Theme.success
                                                 : state === "pending" ? Theme.warning
                                                 : Theme.accent

    clip: true

    Rectangle {
        anchors.fill: parent
        color: "#1207162F"
        radius: 22
    }

    Item {
        id: ringField
        width: Math.max(root.width, root.height) * 1.12
        height: width
        x: root.width * 0.32
        y: (root.height - height) / 2

        Repeater {
            model: ["#092866", "#0B3FA8", "#0C55D8", "#1269F4", "#1E7FFF", "#3499FF"]
            delegate: Rectangle {
                required property int index
                required property color modelData
                anchors.centerIn: parent
                width: parent.width - index * parent.width * 0.125
                height: width
                radius: width / 2
                color: modelData
                opacity: 0.62 + index * 0.055
                border.width: 1
                border.color: "#204FB7FF"
            }
        }

        Rectangle {
            anchors.centerIn: parent
            width: parent.width * 0.25
            height: width
            radius: width / 2
            color: "#71B9FF"
            opacity: 0.74
        }

        Canvas {
            id: arcCanvas
            anchors.fill: parent
            opacity: 0.78
            onPaint: {
                const ctx = getContext("2d")
                ctx.reset()
                const center = width / 2
                const radians = Math.PI / 180
                ctx.lineCap = "round"
                ctx.lineWidth = 3
                ctx.strokeStyle = root.semanticColor
                ctx.shadowColor = root.semanticColor
                ctx.shadowBlur = 12
                ctx.beginPath()
                ctx.arc(center, center, width * 0.43, (root.phase + 18) * radians, (root.phase + 102) * radians)
                ctx.stroke()
                ctx.lineWidth = 1.5
                ctx.beginPath()
                ctx.arc(center, center, width * 0.31, (-root.phase + 205) * radians, (-root.phase + 284) * radians)
                ctx.stroke()
            }
            Connections {
                target: root
                function onPhaseChanged() { arcCanvas.requestPaint() }
                function onSemanticColorChanged() { arcCanvas.requestPaint() }
            }
        }

        scale: root.state === "working" ? 1.025 : 1.0
        Behavior on scale {
            enabled: !root.reducedMotion
            NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
        }
    }

    NumberAnimation on phase {
        from: 0
        to: 360
        duration: root.state === "working" ? 2800 : 10500
        loops: Animation.Infinite
        running: !root.reducedMotion
    }

    Rectangle {
        width: 194
        height: 66
        radius: 18
        color: "#C207142E"
        border.width: 1
        border.color: "#476B9EE4"
        anchors.left: parent.left
        anchors.leftMargin: 26
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 26

        Row {
            anchors.centerIn: parent
            spacing: 12

            Rectangle {
                width: 11
                height: 11
                radius: 6
                color: root.semanticColor
                anchors.verticalCenter: parent.verticalCenter

                SequentialAnimation on opacity {
                    running: root.state === "working" && !root.reducedMotion
                    loops: Animation.Infinite
                    NumberAnimation { to: 0.35; duration: 520 }
                    NumberAnimation { to: 1.0; duration: 520 }
                }
            }

            Column {
                spacing: 2
                Text {
                    text: "JARVIS CORE"
                    color: Theme.muted
                    font.family: Theme.monoFont
                    font.pixelSize: 10
                    font.letterSpacing: 1.4
                }
                Text {
                    text: root.stateLabel
                    color: Theme.text
                    font.family: Theme.bodyFont
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                }
            }
        }
    }
}
