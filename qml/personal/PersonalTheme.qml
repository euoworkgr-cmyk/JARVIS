pragma Singleton
import QtQuick

QtObject {
    // The personal shell consumes semantic tokens only. Future themes can replace
    // this palette without changing page layouts or component behavior.
    property string activeScheme: "olive"

    // Warm graphite and muted olive follow the original personal-assistant reference.
    readonly property color background: "#171916"
    readonly property color backgroundDeep: "#111310"
    readonly property color sidebar: "#1B1D1A"
    readonly property color surface: "#20221E"
    readonly property color surfaceRaised: "#282A24"
    readonly property color surfaceHover: "#32342D"
    readonly property color border: "#3A3D34"
    readonly property color borderStrong: "#505447"
    readonly property color accent: "#B6BB84"
    readonly property color accentBright: "#D0D6A0"
    readonly property color accentMuted: "#7B8156"
    readonly property color accentGhost: "#3B3E33"
    readonly property color text: "#F1EFE7"
    readonly property color muted: "#B4B3AA"
    readonly property color subtle: "#82857A"
    readonly property color success: "#AEBB7E"
    readonly property color warning: "#D7B56F"
    readonly property color danger: "#D9827D"

    readonly property string displayFont: "Georgia"
    readonly property string bodyFont: "Segoe UI"
    readonly property string utilityFont: "Consolas"

    readonly property int radiusSmall: 8
    readonly property int radiusMedium: 12
    readonly property int radiusLarge: 14
    readonly property int spacingSmall: 8
    readonly property int spacingMedium: 16
    readonly property int spacingLarge: 24
    readonly property int motionFast: 140
    readonly property int motionMedium: 220
}
