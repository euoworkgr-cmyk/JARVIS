pragma Singleton
import QtQuick
import ".." as Shared

QtObject {
    // The personal shell consumes semantic tokens only. Future themes can replace
    // this palette without changing page layouts or component behavior.
    property string activeScheme: "dark"
    readonly property bool light: activeScheme === "light"

    // Warm graphite and muted olive follow the original personal-assistant reference.
    readonly property color background: light ? "#F4F1E8" : "#171916"
    readonly property color backgroundDeep: light ? "#E8E3D6" : "#111310"
    readonly property color sidebar: light ? "#ECE7DA" : "#1B1D1A"
    readonly property color surface: light ? "#FBF9F3" : "#20221E"
    readonly property color surfaceRaised: light ? "#FFFFFF" : "#282A24"
    readonly property color surfaceHover: light ? "#E4E0D3" : "#32342D"
    readonly property color border: light ? "#CEC8B8" : "#3A3D34"
    readonly property color borderStrong: light ? "#AAA38F" : "#505447"
    readonly property color accent: light ? "#687044" : "#B6BB84"
    readonly property color accentBright: light ? "#4F572F" : "#D0D6A0"
    readonly property color accentMuted: light ? "#858C62" : "#7B8156"
    readonly property color accentGhost: light ? "#DDE0C8" : "#3B3E33"
    readonly property color text: light ? "#25271F" : "#F1EFE7"
    readonly property color muted: light ? "#5F6259" : "#B4B3AA"
    readonly property color subtle: light ? "#7C7E73" : "#82857A"
    readonly property color success: light ? "#5D6B37" : "#AEBB7E"
    readonly property color warning: light ? "#946B24" : "#D7B56F"
    readonly property color danger: light ? "#A64640" : "#D9827D"
    readonly property color onAccent: light ? "#FFFFFF" : "#17190F"
    readonly property color dangerSurface: light ? "#F4DDDA" : "#3B2927"
    readonly property color dangerSurfaceStrong: light ? "#EBCBC7" : "#56302D"

    readonly property string displayFont: Shared.Theme.displayFont
    readonly property string bodyFont: Shared.Theme.bodyFont
    readonly property string utilityFont: Shared.Theme.bodyFont

    readonly property int hero: Shared.Theme.hero
    readonly property int title: Shared.Theme.title
    readonly property int body: Shared.Theme.body
    readonly property int label: Shared.Theme.label
    readonly property int caption: Shared.Theme.caption
    readonly property int micro: Shared.Theme.micro
    readonly property real lineHeightTight: Shared.Theme.lineHeightTight
    readonly property real lineHeightRelaxed: Shared.Theme.lineHeightRelaxed

    readonly property int radiusSmall: 8
    readonly property int radiusMedium: 12
    readonly property int radiusLarge: 14
    readonly property int spacingSmall: 8
    readonly property int spacingMedium: 16
    readonly property int spacingLarge: 24
    readonly property int durFast: Shared.Theme.durFast
    readonly property int durBase: Shared.Theme.durBase
    readonly property int durSlow: Shared.Theme.durSlow
    readonly property int durFocus: Shared.Theme.durFocus
    readonly property int durProgress: Shared.Theme.durProgress
    readonly property int durPulse: Shared.Theme.durPulse
    readonly property int staggerStep: Shared.Theme.staggerStep
    readonly property int easeOut: Shared.Theme.easeOut
}
