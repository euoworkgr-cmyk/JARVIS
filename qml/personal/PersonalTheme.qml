pragma Singleton
import QtQuick
import ".." as Shared

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
