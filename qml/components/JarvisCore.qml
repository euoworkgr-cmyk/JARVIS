import QtQuick
import QtQuick.Shapes
import ".."

Item {
    id: root
    property string state: "idle"
    property string stateLabel: "Готов к работе"
    property bool reducedMotion: Theme.reducedMotion
    property bool animationEnabled: true

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
        width: Math.round(Math.max(root.width, root.height) * 1.12)
        height: width
        x: Math.round(root.width * 0.32)
        y: Math.round((root.height - height) / 2)

        Repeater {
            model: ["#092866", "#0B3FA8", "#0C55D8", "#1269F4", "#1E7FFF", "#3499FF"]
            delegate: Rectangle {
                required property int index
                required property color modelData
                anchors.centerIn: parent
                width: Math.round(parent.width - index * parent.width * 0.125)
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
            width: Math.round(parent.width * 0.25)
            height: width
            radius: width / 2
            color: "#71B9FF"
            opacity: 0.74
        }

        Shape {
            id: outerArc
            anchors.fill: parent
            layer.enabled: true
            layer.smooth: true

            ShapePath {
                strokeColor: Qt.rgba(root.semanticColor.r, root.semanticColor.g, root.semanticColor.b, 0.18)
                strokeWidth: 11
                capStyle: ShapePath.RoundCap
                fillColor: "transparent"
                PathAngleArc {
                    centerX: outerArc.width / 2
                    centerY: outerArc.height / 2
                    radiusX: outerArc.width * 0.43
                    radiusY: outerArc.height * 0.43
                    startAngle: 18
                    sweepAngle: 84
                }
            }

            ShapePath {
                strokeColor: root.semanticColor
                strokeWidth: 3
                capStyle: ShapePath.RoundCap
                fillColor: "transparent"
                PathAngleArc {
                    centerX: outerArc.width / 2
                    centerY: outerArc.height / 2
                    radiusX: outerArc.width * 0.43
                    radiusY: outerArc.height * 0.43
                    startAngle: 18
                    sweepAngle: 84
                }
            }

            RotationAnimator {
                target: outerArc
                from: 0
                to: 360
                duration: Theme.durAmbientOuter
                loops: Animation.Infinite
                running: root.animationEnabled && !root.reducedMotion && root.state === "working"
            }

        }

        Shape {
            id: innerArc
            anchors.fill: parent
            layer.enabled: true
            layer.smooth: true

            ShapePath {
                strokeColor: Qt.rgba(root.semanticColor.r, root.semanticColor.g, root.semanticColor.b, 0.13)
                strokeWidth: 7
                capStyle: ShapePath.RoundCap
                fillColor: "transparent"
                PathAngleArc {
                    centerX: innerArc.width / 2
                    centerY: innerArc.height / 2
                    radiusX: innerArc.width * 0.31
                    radiusY: innerArc.height * 0.31
                    startAngle: 205
                    sweepAngle: 79
                }
            }

            ShapePath {
                strokeColor: root.semanticColor
                strokeWidth: 1.5
                capStyle: ShapePath.RoundCap
                fillColor: "transparent"
                PathAngleArc {
                    centerX: innerArc.width / 2
                    centerY: innerArc.height / 2
                    radiusX: innerArc.width * 0.31
                    radiusY: innerArc.height * 0.31
                    startAngle: 205
                    sweepAngle: 79
                }
            }

            RotationAnimator {
                target: innerArc
                from: 0
                to: -360
                duration: Theme.durAmbientInner
                loops: Animation.Infinite
                running: root.animationEnabled && !root.reducedMotion && root.state === "working"
            }

        }

        scale: root.state === "working" ? 1.025 : 1.0
        Behavior on scale {
            NumberAnimation { duration: Theme.durBase; easing.type: Theme.easeOut }
        }
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
                    NumberAnimation { to: 0.5; duration: Math.round(Theme.durPulse / 2); easing.type: Easing.InOutSine }
                    NumberAnimation { to: 1.0; duration: Math.round(Theme.durPulse / 2); easing.type: Easing.InOutSine }
                }
            }

            Column {
                spacing: 2
                LabelSharp {
                    text: "JARVIS CORE"
                    color: Theme.muted
                    font.family: Theme.monoFont
                    font.pixelSize: Theme.micro
                    font.letterSpacing: 1.4
                }
                LabelSmooth {
                    text: root.stateLabel
                    color: Theme.text
                    font.family: Theme.bodyFont
                    font.pixelSize: Theme.title
                    font.weight: Font.DemiBold
                }
            }
        }
    }
}
