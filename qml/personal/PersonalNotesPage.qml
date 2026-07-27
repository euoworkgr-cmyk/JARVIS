import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import ".." as Shared

Item {
    id: root

    function noteCountLabel(count) {
        const lastTwo = count % 100
        const last = count % 10
        if (lastTwo >= 11 && lastTwo <= 14)
            return count + " заметок"
        if (last === 1)
            return count + " заметка"
        if (last >= 2 && last <= 4)
            return count + " заметки"
        return count + " заметок"
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 18

        RowLayout {
            Layout.fillWidth: true

            Column {
                spacing: 4
                Shared.LabelSmooth {
                    text: "Заметки"
                    color: PersonalTheme.text
                    font.family: PersonalTheme.displayFont
                    font.pixelSize: PersonalTheme.title
                    font.weight: Font.Medium
                }
                Shared.LabelSharp {
                    text: root.noteCountLabel(backend.noteItems.length)
                          + " · хранятся только на этом компьютере"
                    color: PersonalTheme.muted
                    font.family: PersonalTheme.bodyFont
                    font.pixelSize: PersonalTheme.caption
                }
            }

            Item { Layout.fillWidth: true }

            Button {
                id: clearButton
                visible: backend.noteItems.length > 0
                text: "Очистить всё"
                hoverEnabled: true
                activeFocusOnTab: true
                Accessible.name: text
                onClicked: clearNotesPopup.open()

                contentItem: Shared.LabelSharp {
                    text: clearButton.text
                    color: PersonalTheme.danger
                    font.family: PersonalTheme.bodyFont
                    font.pixelSize: PersonalTheme.label
                    font.weight: Font.Medium
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    implicitWidth: 112
                    implicitHeight: 38
                    radius: PersonalTheme.radiusSmall
                    color: clearButton.hovered ? "#3B2927" : PersonalTheme.surface
                    border.width: clearButton.activeFocus ? 2 : 1
                    border.color: clearButton.activeFocus
                                  ? PersonalTheme.danger : PersonalTheme.border
                }
            }
        }

        PersonalPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 126

            RowLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                TextArea {
                    id: newNote
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    leftPadding: 14
                    rightPadding: 14
                    topPadding: 11
                    bottomPadding: 11
                    color: PersonalTheme.text
                    placeholderText: "Запишите мысль, задачу или напоминание…"
                    placeholderTextColor: PersonalTheme.subtle
                    selectionColor: PersonalTheme.accentMuted
                    selectedTextColor: PersonalTheme.backgroundDeep
                    wrapMode: TextEdit.Wrap
                    font.family: PersonalTheme.bodyFont
                    font.pixelSize: PersonalTheme.body
                    renderType: Text.NativeRendering
                    Accessible.name: "Новая заметка"

                    background: Rectangle {
                        radius: PersonalTheme.radiusSmall
                        color: PersonalTheme.backgroundDeep
                        border.width: newNote.activeFocus ? 2 : 1
                        border.color: newNote.activeFocus
                                      ? PersonalTheme.accent : PersonalTheme.border
                    }

                    Keys.onPressed: function(event) {
                        if (event.key === Qt.Key_Return
                                && (event.modifiers & Qt.ControlModifier)) {
                            addButton.clicked()
                            event.accepted = true
                        }
                    }
                }

                Button {
                    id: addButton
                    Layout.preferredWidth: 124
                    Layout.fillHeight: true
                    enabled: newNote.text.trim().length > 0
                    hoverEnabled: true
                    activeFocusOnTab: true
                    Accessible.name: "Добавить заметку"
                    onClicked: {
                        if (backend.addNote(newNote.text))
                            newNote.text = ""
                    }

                    contentItem: Column {
                        anchors.centerIn: parent
                        spacing: 7
                        PersonalIcon {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: 22
                            height: 22
                            name: "plus"
                            color: addButton.enabled
                                   ? PersonalTheme.backgroundDeep : PersonalTheme.subtle
                        }
                        Shared.LabelSharp {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "Добавить"
                            color: addButton.enabled
                                   ? PersonalTheme.backgroundDeep : PersonalTheme.subtle
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: PersonalTheme.label
                            font.weight: Font.DemiBold
                        }
                    }
                    background: Rectangle {
                        radius: PersonalTheme.radiusSmall
                        color: !addButton.enabled ? PersonalTheme.surfaceHover
                              : addButton.down ? PersonalTheme.accentMuted
                              : addButton.hovered ? PersonalTheme.accentBright
                              : PersonalTheme.accent
                        border.width: addButton.activeFocus ? 2 : 0
                        border.color: PersonalTheme.text
                    }
                }
            }
        }

        PersonalPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Item {
                anchors.fill: parent
                anchors.margins: 16

                Column {
                    visible: backend.noteItems.length === 0
                    anchors.centerIn: parent
                    spacing: 10

                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 54
                        height: 54
                        radius: PersonalTheme.radiusMedium
                        color: PersonalTheme.accentGhost
                        border.width: 1
                        border.color: PersonalTheme.borderStrong
                        PersonalIcon {
                            anchors.centerIn: parent
                            width: 26
                            height: 26
                            name: "notes"
                            color: PersonalTheme.accent
                        }
                    }
                    Shared.LabelSmooth {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "Заметок пока нет"
                        color: PersonalTheme.text
                        font.family: PersonalTheme.displayFont
                        font.pixelSize: PersonalTheme.body
                        font.weight: Font.Medium
                    }
                    Shared.LabelSharp {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "Добавьте первую заметку в поле выше."
                        color: PersonalTheme.muted
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: PersonalTheme.caption
                    }
                }

                ListView {
                    id: notesList
                    anchors.fill: parent
                    visible: count > 0
                    model: backend.noteItems
                    spacing: 10
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: PersonalScrollBar { policy: ScrollBar.AsNeeded }

                    delegate: Rectangle {
                        id: noteCard
                        required property var modelData
                        property bool editing: false
                        width: notesList.width - 12
                        height: editing ? 140 : 78
                        radius: PersonalTheme.radiusMedium
                        color: editing || noteHover.hovered
                               ? PersonalTheme.surfaceHover : PersonalTheme.surface
                        border.width: editing ? 2 : 1
                        border.color: editing
                                      ? PersonalTheme.accent : PersonalTheme.border

                        Behavior on height {
                            NumberAnimation {
                                duration: PersonalTheme.durFocus
                                easing.type: PersonalTheme.easeOut
                            }
                        }

                        Rectangle {
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            width: 3
                            radius: 2
                            color: PersonalTheme.accentMuted
                        }

                        HoverHandler { id: noteHover }

                        Shared.LabelSharp {
                            visible: !noteCard.editing
                            anchors.left: parent.left
                            anchors.leftMargin: 18
                            anchors.right: editButton.left
                            anchors.rightMargin: 14
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.text
                            color: PersonalTheme.text
                            elide: Text.ElideRight
                            maximumLineCount: 2
                            wrapMode: Text.WordWrap
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: PersonalTheme.body
                        }

                        TextArea {
                            id: editField
                            visible: noteCard.editing
                            anchors.left: parent.left
                            anchors.leftMargin: 14
                            anchors.right: parent.right
                            anchors.rightMargin: 14
                            anchors.top: parent.top
                            anchors.topMargin: 10
                            height: 78
                            text: modelData.text
                            color: PersonalTheme.text
                            selectionColor: PersonalTheme.accentMuted
                            selectedTextColor: PersonalTheme.backgroundDeep
                            wrapMode: TextEdit.Wrap
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: PersonalTheme.body
                            renderType: Text.NativeRendering
                            background: Rectangle {
                                radius: PersonalTheme.radiusSmall
                                color: PersonalTheme.backgroundDeep
                                border.width: 1
                                border.color: PersonalTheme.borderStrong
                            }
                        }

                        Row {
                            visible: noteCard.editing
                            anchors.right: parent.right
                            anchors.rightMargin: 14
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 10
                            spacing: 8

                            Button {
                                id: cancelEditButton
                                text: "Отмена"
                                onClicked: {
                                    editField.text = modelData.text
                                    noteCard.editing = false
                                }
                                contentItem: Shared.LabelSharp {
                                    text: cancelEditButton.text
                                    color: PersonalTheme.muted
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: PersonalTheme.caption
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    implicitWidth: 82
                                    implicitHeight: 32
                                    radius: PersonalTheme.radiusSmall
                                    color: cancelEditButton.hovered
                                           ? PersonalTheme.surfaceRaised : PersonalTheme.surface
                                    border.width: 1
                                    border.color: PersonalTheme.border
                                }
                            }

                            Button {
                                id: saveEditButton
                                text: "Сохранить"
                                enabled: editField.text.trim().length > 0
                                onClicked: {
                                    if (backend.updateNote(modelData.index, editField.text))
                                        noteCard.editing = false
                                }
                                contentItem: Shared.LabelSharp {
                                    text: saveEditButton.text
                                    color: PersonalTheme.backgroundDeep
                                    font.family: PersonalTheme.bodyFont
                                    font.pixelSize: PersonalTheme.caption
                                    font.weight: Font.DemiBold
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    implicitWidth: 96
                                    implicitHeight: 32
                                    radius: PersonalTheme.radiusSmall
                                    color: saveEditButton.hovered
                                           ? PersonalTheme.accentBright : PersonalTheme.accent
                                }
                            }
                        }

                        Button {
                            id: editButton
                            visible: !noteCard.editing
                            anchors.right: deleteButton.left
                            anchors.rightMargin: 6
                            anchors.verticalCenter: parent.verticalCenter
                            Accessible.name: "Изменить заметку"
                            onClicked: {
                                editField.text = modelData.text
                                noteCard.editing = true
                                editField.forceActiveFocus()
                            }
                            contentItem: PersonalIcon {
                                name: "edit"
                                color: editButton.hovered
                                       ? PersonalTheme.text : PersonalTheme.muted
                            }
                            background: Rectangle {
                                implicitWidth: 36
                                implicitHeight: 36
                                radius: PersonalTheme.radiusSmall
                                color: editButton.hovered
                                       ? PersonalTheme.surfaceRaised : "transparent"
                            }
                        }

                        Button {
                            id: deleteButton
                            visible: !noteCard.editing
                            anchors.right: parent.right
                            anchors.rightMargin: 12
                            anchors.verticalCenter: parent.verticalCenter
                            Accessible.name: "Удалить заметку"
                            onClicked: backend.removeNote(modelData.index)
                            contentItem: PersonalIcon {
                                name: "delete"
                                color: deleteButton.hovered
                                       ? PersonalTheme.danger : PersonalTheme.muted
                            }
                            background: Rectangle {
                                implicitWidth: 36
                                implicitHeight: 36
                                radius: PersonalTheme.radiusSmall
                                color: deleteButton.hovered ? "#3B2927" : "transparent"
                            }
                        }
                    }
                }
            }
        }
    }

    Popup {
        id: clearNotesPopup
        width: Math.round(Math.min(430, root.width - 60))
        height: 226
        anchors.centerIn: Overlay.overlay
        modal: true
        focus: true
        closePolicy: Popup.NoAutoClose
        padding: 0

        background: Rectangle {
            radius: PersonalTheme.radiusLarge
            color: PersonalTheme.surfaceRaised
            border.width: 1
            border.color: PersonalTheme.borderStrong
        }

        contentItem: ColumnLayout {
            anchors.fill: parent
            anchors.margins: 22
            spacing: 12

            Shared.LabelSmooth {
                Layout.fillWidth: true
                text: "Очистить все заметки?"
                color: PersonalTheme.text
                wrapMode: Text.WordWrap
                font.family: PersonalTheme.displayFont
                font.pixelSize: PersonalTheme.title
            }
            Shared.LabelSharp {
                Layout.fillWidth: true
                text: "Все локальные заметки будут удалены без возможности восстановления."
                color: PersonalTheme.muted
                wrapMode: Text.WordWrap
                font.family: PersonalTheme.bodyFont
                font.pixelSize: PersonalTheme.caption
            }

            Item { Layout.fillHeight: true }

            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button {
                    id: cancelClearButton
                    text: "Отмена"
                    onClicked: clearNotesPopup.close()
                    contentItem: Shared.LabelSharp {
                        text: cancelClearButton.text
                        color: PersonalTheme.muted
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: PersonalTheme.label
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        implicitWidth: 96
                        implicitHeight: 38
                        radius: PersonalTheme.radiusSmall
                        color: cancelClearButton.hovered
                               ? PersonalTheme.surfaceHover : PersonalTheme.surface
                        border.width: 1
                        border.color: PersonalTheme.border
                    }
                }
                Button {
                    id: confirmClearButton
                    text: "Очистить"
                    onClicked: {
                        if (backend.clearNotes())
                            clearNotesPopup.close()
                    }
                    contentItem: Shared.LabelSharp {
                        text: confirmClearButton.text
                        color: PersonalTheme.text
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: PersonalTheme.label
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        implicitWidth: 104
                        implicitHeight: 38
                        radius: PersonalTheme.radiusSmall
                        color: confirmClearButton.hovered ? "#56302D" : "#452725"
                        border.width: 1
                        border.color: PersonalTheme.danger
                    }
                }
            }
        }
    }
}
