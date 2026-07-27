import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            Column {
                spacing: 3
                Text {
                    text: "ЗАМЕТКИ"
                    color: Theme.text
                    font.family: Theme.headingFont
                    font.pixelSize: 25
                    font.weight: Font.DemiBold
                    font.letterSpacing: 0.8
                }
                Text {
                    text: backend.noteItems.length + " заметок · хранятся только на этом компьютере"
                    color: Theme.muted
                    font.family: Theme.bodyFont
                    font.pixelSize: 13
                }
            }
            Item { Layout.fillWidth: true }
            ActionButton {
                text: "Очистить всё"
                danger: true
                visible: backend.noteItems.length > 0
                onClicked: clearNotesPopup.open()
            }
        }

        GlassPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 132

            RowLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 12

                TextArea {
                    id: newNote
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    leftPadding: 15
                    rightPadding: 15
                    topPadding: 12
                    bottomPadding: 12
                    color: Theme.text
                    placeholderText: "Запишите мысль, задачу или напоминание…"
                    placeholderTextColor: "#7388B2"
                    wrapMode: TextEdit.Wrap
                    font.family: Theme.bodyFont
                    font.pixelSize: 13
                    Accessible.name: "Новая заметка"
                    background: Rectangle {
                        radius: 13
                        color: "#B4081734"
                        border.width: newNote.activeFocus ? 1.5 : 1
                        border.color: newNote.activeFocus ? Theme.accent : Theme.border
                    }
                    Keys.onPressed: function(event) {
                        if (event.key === Qt.Key_Return && (event.modifiers & Qt.ControlModifier)) {
                            addButton.clicked()
                            event.accepted = true
                        }
                    }
                }

                ActionButton {
                    id: addButton
                    Layout.preferredWidth: 130
                    Layout.fillHeight: true
                    text: "Добавить"
                    accent: true
                    enabled: newNote.text.trim().length > 0
                    accessibleName: "Добавить заметку"
                    onClicked: {
                        if (backend.addNote(newNote.text))
                            newNote.text = ""
                    }
                }
            }
        }

        GlassPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Item {
                anchors.fill: parent
                anchors.margins: 18

                Column {
                    visible: backend.noteItems.length === 0
                    anchors.centerIn: parent
                    spacing: 9
                    Rectangle {
                        width: 56
                        height: 56
                        radius: 18
                        color: "#2538A7FF"
                        anchors.horizontalCenter: parent.horizontalCenter
                        Image {
                            anchors.centerIn: parent
                            source: Qt.resolvedUrl("../../assets/icons/notes.svg")
                            sourceSize.width: 25
                            sourceSize.height: 25
                        }
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "Заметок пока нет"
                        color: Theme.text
                        font.family: Theme.bodyFont
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "Добавьте первую заметку в поле выше."
                        color: Theme.muted
                        font.family: Theme.bodyFont
                        font.pixelSize: 12
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
                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                    delegate: Rectangle {
                        id: noteCard
                        required property var modelData
                        property bool editing: false
                        width: notesList.width - 12
                        height: editing ? 132 : 76
                        radius: 14
                        color: noteHover.hovered || editing ? "#C0132B58" : "#960C1C3D"
                        border.width: 1
                        border.color: editing ? Theme.accent : (noteHover.hovered ? Theme.borderStrong : Theme.border)

                        Behavior on height {
                            enabled: !backend.reducedMotion
                            NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
                        }

                        HoverHandler { id: noteHover }

                        Text {
                            visible: !noteCard.editing
                            anchors.left: parent.left
                            anchors.leftMargin: 18
                            anchors.right: editButton.left
                            anchors.rightMargin: 14
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.text
                            color: Theme.text
                            elide: Text.ElideRight
                            maximumLineCount: 2
                            wrapMode: Text.WordWrap
                            font.family: Theme.bodyFont
                            font.pixelSize: 13
                        }

                        TextArea {
                            id: editField
                            visible: noteCard.editing
                            anchors.left: parent.left
                            anchors.leftMargin: 12
                            anchors.right: parent.right
                            anchors.rightMargin: 12
                            anchors.top: parent.top
                            anchors.topMargin: 10
                            height: 72
                            text: modelData.text
                            color: Theme.text
                            wrapMode: TextEdit.Wrap
                            font.family: Theme.bodyFont
                            font.pixelSize: 13
                            background: Rectangle {
                                radius: 10
                                color: "#C507142E"
                                border.width: 1
                                border.color: Theme.borderStrong
                            }
                        }

                        Row {
                            visible: noteCard.editing
                            anchors.right: parent.right
                            anchors.rightMargin: 12
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 10
                            spacing: 8
                            ActionButton {
                                text: "Отмена"
                                implicitWidth: 92
                                implicitHeight: 34
                                onClicked: {
                                    editField.text = modelData.text
                                    noteCard.editing = false
                                }
                            }
                            ActionButton {
                                text: "Сохранить"
                                accent: true
                                implicitWidth: 104
                                implicitHeight: 34
                                enabled: editField.text.trim().length > 0
                                onClicked: {
                                    if (backend.updateNote(modelData.index, editField.text))
                                        noteCard.editing = false
                                }
                            }
                        }

                        ActionButton {
                            id: editButton
                            visible: !noteCard.editing
                            anchors.right: deleteButton.left
                            anchors.rightMargin: 8
                            anchors.verticalCenter: parent.verticalCenter
                            text: "Изменить"
                            implicitWidth: 102
                            implicitHeight: 36
                            onClicked: {
                                editField.text = modelData.text
                                noteCard.editing = true
                                editField.forceActiveFocus()
                            }
                        }
                        ActionButton {
                            id: deleteButton
                            visible: !noteCard.editing
                            anchors.right: parent.right
                            anchors.rightMargin: 12
                            anchors.verticalCenter: parent.verticalCenter
                            text: "Удалить"
                            danger: true
                            implicitWidth: 92
                            implicitHeight: 36
                            onClicked: backend.removeNote(modelData.index)
                        }
                    }
                }
            }
        }
    }

    Popup {
        id: clearNotesPopup
        width: 420
        height: 236
        anchors.centerIn: Overlay.overlay
        modal: true
        focus: true
        closePolicy: Popup.NoAutoClose
        padding: 0
        background: Rectangle {
            radius: 20
            color: Theme.panelStrong
            border.width: 1
            border.color: Theme.borderStrong
        }
        contentItem: ColumnLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 13
            Text {
                Layout.fillWidth: true
                text: "Очистить все заметки?"
                color: Theme.text
                wrapMode: Text.WordWrap
                font.family: Theme.headingFont
                font.pixelSize: 21
                font.weight: Font.DemiBold
            }
            Text {
                Layout.fillWidth: true
                text: "Это действие удалит все локальные заметки без возможности восстановления."
                color: Theme.muted
                wrapMode: Text.WordWrap
                font.family: Theme.bodyFont
                font.pixelSize: 13
            }
            Item { Layout.fillHeight: true }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                ActionButton { text: "Отмена"; onClicked: clearNotesPopup.close() }
                ActionButton {
                    text: "Очистить"
                    danger: true
                    onClicked: {
                        if (backend.clearNotes())
                            clearNotesPopup.close()
                    }
                }
            }
        }
    }
}
