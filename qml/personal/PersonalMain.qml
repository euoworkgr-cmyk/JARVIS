import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "."

ApplicationWindow {
    id: window
    width: 1180
    height: 760
    minimumWidth: 1000
    minimumHeight: 680
    visible: false
    color: PersonalTheme.backgroundDeep
    flags: Qt.Window | Qt.FramelessWindowHint
    title: "JARVIS Personal"
    property bool windowMoving: false

    onClosing: function(close) {
        if (!backend.quitting) {
            close.accepted = false
            window.hide()
        }
    }

    Connections {
        target: backend
        function onHelpRequested() { backend.setPage("settings") }
        function onPendingActionChanged() {
            if (backend.pendingAction.pending_id)
                confirmPopup.open()
            else
                confirmPopup.close()
        }
    }

    background: Rectangle {
        radius: window.visibility === Window.Maximized ? 0 : PersonalTheme.radiusLarge
        color: PersonalTheme.background
        border.width: 1
        border.color: PersonalTheme.borderStrong
    }

    Item {
        anchors.fill: parent
        anchors.margins: window.visibility === Window.Maximized ? 0 : 1

        Rectangle {
            id: titleBar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 54
            color: PersonalTheme.backgroundDeep
            radius: window.visibility === Window.Maximized ? 0 : PersonalTheme.radiusLarge

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: PersonalTheme.border
            }

            Row {
                anchors.left: parent.left
                anchors.leftMargin: 18
                anchors.verticalCenter: parent.verticalCenter
                spacing: 10

                Item {
                    width: 28
                    height: 28
                    Canvas {
                        anchors.fill: parent
                        antialiasing: true
                        onPaint: {
                            const context = getContext("2d")
                            context.reset()
                            context.strokeStyle = PersonalTheme.accent
                            context.lineWidth = 1.5
                            context.beginPath()
                            context.moveTo(7, 23)
                            context.bezierCurveTo(7, 11, 13, 5, 23, 3)
                            context.bezierCurveTo(23, 14, 18, 22, 7, 23)
                            context.stroke()
                            context.beginPath()
                            context.moveTo(8, 23)
                            context.lineTo(21, 6)
                            context.stroke()
                        }
                    }
                }
                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                        text: "Голосовой помощник"
                        color: PersonalTheme.text
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: 13
                    }
                }
            }

            Row {
                id: windowButtons
                anchors.right: parent.right
                anchors.top: parent.top
                height: parent.height

                Repeater {
                    model: [
                        { symbol: "—", label: "Свернуть", action: "minimize" },
                        { symbol: "□", label: "Развернуть", action: "maximize" },
                        { symbol: "×", label: "Скрыть в трей", action: "close" }
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        width: 48
                        height: titleBar.height
                        color: buttonHover.hovered
                               ? (modelData.action === "close" ? "#55302E" : PersonalTheme.surfaceHover)
                               : "transparent"
                        Accessible.role: Accessible.Button
                        Accessible.name: modelData.label
                        Text {
                            anchors.centerIn: parent
                            text: modelData.symbol
                            color: PersonalTheme.muted
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: modelData.action === "close" ? 20 : 16
                        }
                        HoverHandler { id: buttonHover }
                        TapHandler {
                            onTapped: {
                                if (modelData.action === "minimize")
                                    window.showMinimized()
                                else if (modelData.action === "maximize")
                                    window.visibility === Window.Maximized ? window.showNormal() : window.showMaximized()
                                else
                                    window.hide()
                            }
                        }
                    }
                }
            }

            DragHandler {
                target: null
                grabPermissions: PointerHandler.CanTakeOverFromAnything
                onActiveChanged: {
                    window.windowMoving = active
                    if (active && window.visibility !== Window.Maximized)
                        window.startSystemMove()
                }
            }
            TapHandler {
                acceptedButtons: Qt.LeftButton
                gesturePolicy: TapHandler.DragThreshold
                onDoubleTapped: window.visibility === Window.Maximized ? window.showNormal() : window.showMaximized()
            }
        }

        Rectangle {
            id: sidebar
            anchors.left: parent.left
            anchors.top: titleBar.bottom
            anchors.bottom: parent.bottom
            width: 188
            color: PersonalTheme.sidebar

            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: PersonalTheme.border
            }

            Column {
                anchors.left: parent.left
                anchors.leftMargin: 14
                anchors.top: parent.top
                anchors.topMargin: 28
                spacing: 10

                PersonalNavButton {
                    iconName: "home"
                    label: "Главная"
                    selected: backend.currentPage === "home"
                    onClicked: backend.setPage("home")
                }
                PersonalNavButton {
                    iconName: "statistics"
                    label: "Статистика"
                    selected: backend.currentPage === "statistics"
                    onClicked: backend.setPage("statistics")
                }
                PersonalNavButton {
                    iconName: "customization"
                    label: "Кастомизация"
                    selected: backend.currentPage === "customization"
                    onClicked: backend.setPage("customization")
                }
                PersonalNavButton {
                    iconName: "settings"
                    label: "Настройки"
                    selected: backend.currentPage === "settings"
                    onClicked: backend.setPage("settings")
                }
            }

        }

        StackLayout {
            anchors.left: sidebar.right
            anchors.right: parent.right
            anchors.top: titleBar.bottom
            anchors.bottom: parent.bottom
            anchors.leftMargin: 30
            anchors.rightMargin: 30
            anchors.topMargin: 20
            anchors.bottomMargin: 20
            currentIndex: backend.currentPage === "statistics" ? 1
                        : backend.currentPage === "customization" ? 2
                        : backend.currentPage === "settings" ? 3 : 0

            PersonalHomePage { }
            PersonalStatisticsPage { }
            PersonalPlaceholderPage {
                pageTitle: "Кастомизация"
                pageDescription: "Здесь появятся темы, фоновые рисунки и параметры визуального поведения. Структура personal-версии уже отделена от палитры, поэтому новые темы не потребуют переделки экранов."
                symbol: "◌"
            }
            PersonalPlaceholderPage {
                pageTitle: "Настройки"
                pageDescription: "Здесь будут системные параметры, голосовое управление и раздел Extra. Наполнение определим отдельно, не смешивая настройки с ежедневными действиями."
                symbol: "⚙"
            }
        }
    }

    Rectangle {
        id: toast
        z: 900
        width: Math.min(420, window.width - 80)
        height: backend.lastMessage.detail ? 78 : 62
        radius: PersonalTheme.radiusMedium
        color: PersonalTheme.surfaceRaised
        border.width: 1
        border.color: backend.lastMessage.status === "error" || backend.lastMessage.status === "not_found"
                      ? PersonalTheme.danger : backend.lastMessage.status === "success"
                      ? PersonalTheme.success : PersonalTheme.borderStrong
        anchors.right: parent.right
        anchors.rightMargin: 24
        anchors.bottom: parent.bottom
        anchors.bottomMargin: backend.lastMessage.title ? 24 : -height - 10

        Behavior on anchors.bottomMargin {
            enabled: !backend.reducedMotion
            NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
        }

        Column {
            anchors.left: parent.left
            anchors.leftMargin: 18
            anchors.right: closeToast.left
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            spacing: 4
            Text {
                width: parent.width
                text: backend.lastMessage.title || ""
                color: PersonalTheme.text
                elide: Text.ElideRight
                font.family: PersonalTheme.bodyFont
                font.pixelSize: 12
                font.weight: Font.DemiBold
            }
            Text {
                width: parent.width
                visible: text.length > 0
                text: backend.lastMessage.detail || ""
                color: PersonalTheme.muted
                elide: Text.ElideRight
                font.family: PersonalTheme.bodyFont
                font.pixelSize: 10
            }
        }
        Rectangle {
            id: closeToast
            width: 30
            height: 30
            radius: 8
            color: closeToastHover.hovered ? PersonalTheme.surfaceHover : "transparent"
            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            Text {
                anchors.centerIn: parent
                text: "×"
                color: PersonalTheme.muted
                font.pixelSize: 18
            }
            HoverHandler { id: closeToastHover }
            TapHandler { onTapped: backend.dismissMessage() }
        }
    }

    Popup {
        id: confirmPopup
        width: Math.min(510, window.width - 80)
        height: Math.min(420, Math.max(254, confirmContent.implicitHeight + 42))
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
            id: confirmContent
            anchors.fill: parent
            anchors.margins: 22
            spacing: 14

            Text {
                Layout.fillWidth: true
                text: backend.pendingAction.title || "Подтвердите действие"
                color: PersonalTheme.text
                wrapMode: Text.WordWrap
                font.family: PersonalTheme.displayFont
                font.pixelSize: 24
            }
            Text {
                Layout.fillWidth: true
                text: backend.pendingAction.detail || ""
                color: PersonalTheme.muted
                wrapMode: Text.WordWrap
                font.family: PersonalTheme.bodyFont
                font.pixelSize: 12
            }

            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: backend.pendingAction.candidates && backend.pendingAction.candidates.length > 0
                model: backend.pendingAction.candidates || []
                spacing: 6
                clip: true
                delegate: Rectangle {
                    required property var modelData
                    width: ListView.view.width
                    height: 42
                    radius: PersonalTheme.radiusSmall
                    color: PersonalTheme.surface
                    border.width: 1
                    border.color: PersonalTheme.border
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        Text {
                            text: modelData.name
                            color: PersonalTheme.text
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: 11
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            text: "PID " + modelData.pid
                            color: PersonalTheme.subtle
                            font.family: PersonalTheme.utilityFont
                            font.pixelSize: 9
                        }
                    }
                }
            }

            Item { Layout.fillHeight: true }

            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button {
                    text: "Отмена"
                    enabled: !backend.busy
                    onClicked: backend.cancelPending()
                    contentItem: Text {
                        text: parent.text
                        color: PersonalTheme.text
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        implicitWidth: 104
                        implicitHeight: 40
                        radius: PersonalTheme.radiusSmall
                        color: parent.hovered ? PersonalTheme.surfaceHover : PersonalTheme.surface
                        border.width: 1
                        border.color: PersonalTheme.border
                    }
                }
                Button {
                    text: backend.busy ? "Выполняю…" : "Подтвердить"
                    enabled: !backend.busy
                    onClicked: backend.confirmPending()
                    contentItem: Text {
                        text: parent.text
                        color: PersonalTheme.backgroundDeep
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        implicitWidth: 122
                        implicitHeight: 40
                        radius: PersonalTheme.radiusSmall
                        color: parent.hovered ? PersonalTheme.text : PersonalTheme.accent
                    }
                }
            }
        }
    }
}
