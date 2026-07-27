import QtQuick
import "."

Text {
    id: root

    property bool serif: false

    font.family: serif ? Theme.displayFont : Theme.bodyFont
    font.pixelSize: Theme.body
    lineHeightMode: Text.ProportionalHeight
    lineHeight: font.pixelSize >= Theme.title
                ? Theme.lineHeightTight : Theme.lineHeightRelaxed
    renderType: Text.NativeRendering
}
