pragma Singleton
import QtQuick

QtObject {
    // The personal shell consumes semantic tokens only. Future themes can replace
    // this palette without changing page layouts or component behavior.
    property string activeScheme: "forest"

    readonly property color background: activeScheme === "forest" ? "#141714" : "#171717"
    readonly property color backgroundDeep: activeScheme === "forest" ? "#0E100F" : "#101010"
    readonly property color sidebar: activeScheme === "forest" ? "#171A18" : "#151515"
    readonly property color surface: activeScheme === "forest" ? "#1C201D" : "#202020"
    readonly property color surfaceRaised: activeScheme === "forest" ? "#222722" : "#272727"
    readonly property color surfaceHover: activeScheme === "forest" ? "#2A302A" : "#303030"
    readonly property color border: activeScheme === "forest" ? "#343A34" : "#3A3A3A"
    readonly property color borderStrong: activeScheme === "forest" ? "#4B5349" : "#565656"
    readonly property color accent: activeScheme === "forest" ? "#ADB981" : "#B7B7B7"
    readonly property color accentMuted: activeScheme === "forest" ? "#707A54" : "#777777"
    readonly property color text: activeScheme === "forest" ? "#F0EEE6" : "#F2F2F2"
    readonly property color muted: activeScheme === "forest" ? "#A3A79E" : "#A7A7A7"
    readonly property color subtle: activeScheme === "forest" ? "#737970" : "#767676"
    readonly property color success: "#9FBC83"
    readonly property color warning: "#D2B477"
    readonly property color danger: "#D3837F"

    readonly property string displayFont: "Georgia"
    readonly property string bodyFont: "Segoe UI Variable"
    readonly property string utilityFont: "Cascadia Mono"

    readonly property int radiusSmall: 8
    readonly property int radiusMedium: 12
    readonly property int radiusLarge: 16
    readonly property int spacingSmall: 8
    readonly property int spacingMedium: 14
    readonly property int spacingLarge: 24
}
