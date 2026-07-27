pragma Singleton
import QtQuick

QtObject {
    readonly property color background: "#07122D"
    readonly property color backgroundDeep: "#03091A"
    readonly property color panel: "#C20B1C43"
    readonly property color panelStrong: "#E60A1734"
    readonly property color panelHover: "#D6142D5C"
    readonly property color border: "#405B82BC"
    readonly property color borderStrong: "#6F7FB2FF"
    readonly property color primary: "#1668FF"
    readonly property color accent: "#38A7FF"
    readonly property color text: "#F4F7FF"
    readonly property color muted: "#8EA4CF"
    readonly property color success: "#42D392"
    readonly property color danger: "#FF5D6C"
    readonly property color warning: "#F3B85B"

    // Segoe UI Variable is the primary Windows UI face. Qt falls back to
    // Segoe UI when the variable family is unavailable.
    readonly property string displayFont: "Georgia"
    readonly property string bodyFont: "Segoe UI Variable"
    readonly property string bodyFontFallback: "Segoe UI"
    readonly property string headingFont: bodyFont
    readonly property string monoFont: bodyFont

    // The project uses exactly these six type roles. Components must reference
    // the role tokens instead of introducing local pixel sizes.
    readonly property int hero: 26
    readonly property int title: 15
    readonly property int body: 13
    readonly property int label: 12
    readonly property int caption: 11
    readonly property int micro: 10
    readonly property real lineHeightTight: 1.2
    readonly property real lineHeightRelaxed: 1.45

    // Motion tokens collapse to zero when reduced motion is enabled, so every
    // animation can use a shared duration without duplicating conditionals.
    property bool reducedMotion: false
    readonly property int durFast: reducedMotion ? 0 : 130
    readonly property int durBase: reducedMotion ? 0 : 200
    readonly property int durSlow: reducedMotion ? 0 : 260
    readonly property int durFocus: reducedMotion ? 0 : 180
    readonly property int durProgress: reducedMotion ? 0 : 600
    readonly property int durPulse: reducedMotion ? 0 : 1600
    readonly property int durAmbientOuter: reducedMotion ? 0 : 2600
    readonly property int durAmbientInner: reducedMotion ? 0 : 3400
    readonly property int staggerStep: reducedMotion ? 0 : 40
    readonly property int easeOut: Easing.OutCubic
}
