import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "."
import "components"
import "pages"

ApplicationWindow {
    id: window
    width: 1160
    height: 720
    minimumWidth: 960
    minimumHeight: 620
    visible: false
    color: Theme.backgroundDeep
    flags: Qt.Window | Qt.FramelessWindowHint
    title: "JARVIS Desktop"
    property bool windowMoving: false

    onClosing: function(close) {
        if (!backend.quitting) {
            close.accepted = false
            window.hide()
        }
    }

    Connections {
        target: backend
        function onHelpRequested() { helpPopup.open() }
        function onPendingActionChanged() {
            if (backend.pendingAction.pending_id)
                confirmPopup.open()
            else
                confirmPopup.close()
        }
    }

    background: Rectangle {
        radius: window.visibility === Window.Maximized ? 0 : 16
        border.width: 1
        border.color: Theme.borderStrong
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#0A1D48" }
            GradientStop { position: 0.5; color: Theme.background }
            GradientStop { position: 1.0; color: Theme.backgroundDeep }
        }

        Rectangle {
            width: parent.width * 0.55
            height: width
            radius: width / 2
            x: parent.width * 0.62
            y: -height * 0.64
            color: "#17166CFF"
        }
        Rectangle {
            width: parent.width * 0.42
            height: width
            radius: width / 2
            x: -width * 0.66
            y: parent.height * 0.62
            color: "#112F9DFF"
        }
    }

    Item {
        anchors.fill: parent
        anchors.margins: window.visibility === Window.Maximized ? 0 : 1

        Rectangle {
            id: titleBar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 70
            color: "#B3071635"
            radius: window.visibility === Window.Maximized ? 0 : 15

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: "#315A82BC"
            }

            Row {
                anchors.left: parent.left
                anchors.leftMargin: 22
                anchors.verticalCenter: parent.verticalCenter
                spacing: 13

                Rectangle {
                    width: 38
                    height: 38
                    radius: 12
                    gradient: Gradient {
                        GradientStop { position: 0; color: Theme.accent }
                        GradientStop { position: 1; color: Theme.primary }
                    }
                    Text {
                        anchors.centerIn: parent
                        text: "J"
                        color: Theme.text
                        font.family: Theme.headingFont
                        font.pixelSize: 20
                        font.weight: Font.Bold
                    }
                }

                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 0
                    Text {
                        text: "JARVIS"
                        color: Theme.text
                        font.family: Theme.headingFont
                        font.pixelSize: 20
                        font.weight: Font.Bold
                        font.letterSpacing: 1.1
                    }
                    Text {
                        text: "DESKTOP COMMAND CENTER"
                        color: Theme.muted
                        font.family: Theme.monoFont
                        font.pixelSize: 8
                        font.letterSpacing: 1.2
                    }
                }
            }

            Rectangle {
                width: 154
                height: 32
                radius: 16
                color: "#17244B"
                border.width: 1
                border.color: "#355C83B9"
                anchors.right: windowButtons.left
                anchors.rightMargin: 24
                anchors.verticalCenter: parent.verticalCenter

                Row {
                    anchors.centerIn: parent
                    spacing: 9
                    Rectangle {
                        width: 8
                        height: 8
                        radius: 4
                        color: backend.jarvisState === "error" ? Theme.danger
                              : backend.jarvisState === "pending" ? Theme.warning
                              : backend.busy ? Theme.accent : Theme.success
                    }
                    Text {
                        text: backend.stateLabel
                        color: Theme.text
                        font.family: Theme.bodyFont
                        font.pixelSize: 11
                    }
                }
            }

            Row {
                id: windowButtons
                anchors.right: parent.right
                anchors.rightMargin: 12
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
                        height: 42
                        color: buttonHover.hovered
                               ? (modelData.action === "close" ? "#C03B425A" : "#243867")
                               : "transparent"
                        Accessible.role: Accessible.Button
                        Accessible.name: modelData.label
                        Text {
                            anchors.centerIn: parent
                            text: modelData.symbol
                            color: Theme.text
                            font.family: Theme.bodyFont
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

        RowLayout {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: titleBar.bottom
            anchors.bottom: parent.bottom
            anchors.margins: 16
            anchors.topMargin: 14
            spacing: 16

            GlassPanel {
                Layout.preferredWidth: 76
                Layout.fillHeight: true

                Column {
                    anchors.top: parent.top
                    anchors.topMargin: 18
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 12

                    NavButton {
                        iconSource: Qt.resolvedUrl("../assets/icons/home.svg")
                        label: "Главная"
                        selected: backend.currentPage === "home"
                        onClicked: backend.setPage("home")
                    }
                    NavButton {
                        iconSource: Qt.resolvedUrl("../assets/icons/apps.svg")
                        label: "Приложения"
                        selected: backend.currentPage === "apps"
                        onClicked: backend.setPage("apps")
                    }
                    NavButton {
                        iconSource: Qt.resolvedUrl("../assets/icons/game.svg")
                        label: "Игровой режим"
                        selected: backend.currentPage === "game"
                        onClicked: backend.setPage("game")
                    }
                    NavButton {
                        iconSource: Qt.resolvedUrl("../assets/icons/notes.svg")
                        label: "Заметки"
                        selected: backend.currentPage === "notes"
                        onClicked: backend.setPage("notes")
                    }
                }

                NavButton {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 18
                    iconSource: Qt.resolvedUrl("../assets/icons/help.svg")
                    label: "Справка"
                    onClicked: helpPopup.open()
                }
            }

            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: backend.currentPage === "apps" ? 1
                            : backend.currentPage === "game" ? 2
                            : backend.currentPage === "notes" ? 3 : 0

                HomePage {
                    animationEnabled: window.visible
                                      && window.visibility !== Window.Minimized
                                      && !window.windowMoving
                }
                AppsPage { }
                GamePage { }
                NotesPage { }
            }
        }
    }

    Rectangle {
        id: toast
        z: 900
        width: Math.min(430, window.width - 80)
        height: backend.lastMessage.detail ? 82 : 66
        radius: 16
        color: Theme.panelStrong
        border.width: 1
        border.color: backend.lastMessage.status === "error" || backend.lastMessage.status === "not_found"
                      ? "#8FFF5D6C" : backend.lastMessage.status === "success"
                      ? "#7F42D392" : Theme.borderStrong
        anchors.right: parent.right
        anchors.rightMargin: 24
        anchors.bottom: parent.bottom
        anchors.bottomMargin: backend.lastMessage.title ? 24 : -height - 10
        visible: anchors.bottomMargin > -height

        Behavior on anchors.bottomMargin {
            enabled: !backend.reducedMotion
            NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
        }

        readonly property color statusColor: backend.lastMessage.status === "error" || backend.lastMessage.status === "not_found"
                                             ? Theme.danger : backend.lastMessage.status === "success"
                                             ? Theme.success : Theme.accent

        Rectangle {
            width: 4
            height: parent.height - 22
            radius: 2
            color: toast.statusColor
            anchors.left: parent.left
            anchors.leftMargin: 12
            anchors.verticalCenter: parent.verticalCenter
        }
        Column {
            anchors.left: parent.left
            anchors.leftMargin: 28
            anchors.right: closeToast.left
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            spacing: 4
            Text {
                width: parent.width
                text: backend.lastMessage.title || ""
                color: Theme.text
                elide: Text.ElideRight
                font.family: Theme.bodyFont
                font.pixelSize: 13
                font.weight: Font.DemiBold
            }
            Text {
                width: parent.width
                visible: text.length > 0
                text: backend.lastMessage.detail || ""
                color: Theme.muted
                elide: Text.ElideRight
                font.family: Theme.bodyFont
                font.pixelSize: 11
            }
        }
        Rectangle {
            id: closeToast
            width: 30
            height: 30
            radius: 9
            color: closeToastHover.hovered ? "#263A68" : "transparent"
            anchors.right: parent.right
            anchors.rightMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            Text { anchors.centerIn: parent; text: "×"; color: Theme.muted; font.pixelSize: 18 }
            HoverHandler { id: closeToastHover }
            TapHandler { onTapped: backend.dismissMessage() }
        }
    }

    Popup {
        id: confirmPopup
        width: Math.min(520, window.width - 80)
        height: Math.min(430, Math.max(260, confirmContent.implicitHeight + 44))
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
            id: confirmContent
            anchors.fill: parent
            anchors.margins: 24
            spacing: 16

            Rectangle {
                width: 46
                height: 46
                radius: 15
                color: "#2CF3B85B"
                Text {
                    anchors.centerIn: parent
                    text: "!"
                    color: Theme.warning
                    font.family: Theme.headingFont
                    font.pixelSize: 24
                    font.weight: Font.Bold
                }
            }

            Text {
                Layout.fillWidth: true
                text: backend.pendingAction.title || "Подтвердите действие"
                color: Theme.text
                wrapMode: Text.WordWrap
                font.family: Theme.headingFont
                font.pixelSize: 22
                font.weight: Font.DemiBold
            }
            Text {
                Layout.fillWidth: true
                text: backend.pendingAction.detail || ""
                color: Theme.muted
                wrapMode: Text.WordWrap
                font.family: Theme.bodyFont
                font.pixelSize: 14
            }

            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: backend.pendingAction.candidates && backend.pendingAction.candidates.length > 0
                model: backend.pendingAction.candidates || []
                spacing: 7
                clip: true
                delegate: Rectangle {
                    required property var modelData
                    width: ListView.view.width
                    height: 46
                    radius: 11
                    color: "#A30A1835"
                    border.width: 1
                    border.color: Theme.border
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        Text {
                            text: modelData.name
                            color: Theme.text
                            font.family: Theme.bodyFont
                            font.pixelSize: 13
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            text: "PID " + modelData.pid + "  ·  " + modelData.reason
                            color: Theme.muted
                            font.family: Theme.monoFont
                            font.pixelSize: 10
                        }
                    }
                }
            }

            Item { Layout.fillHeight: !confirmPopup.visible }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Item { Layout.fillWidth: true }
                Button {
                    text: "Отмена"
                    enabled: !backend.busy
                    onClicked: backend.cancelPending()
                    contentItem: Text {
                        text: parent.text
                        color: Theme.text
                        font.family: Theme.bodyFont
                        font.pixelSize: 13
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        implicitWidth: 112
                        implicitHeight: 42
                        radius: 12
                        color: parent.hovered ? "#243867" : "#18284C"
                        border.width: 1
                        border.color: Theme.border
                    }
                }
                Button {
                    text: backend.busy ? "Выполняю…" : "Подтвердить"
                    enabled: !backend.busy
                    onClicked: backend.confirmPending()
                    contentItem: Text {
                        text: parent.text
                        color: Theme.text
                        font.family: Theme.bodyFont
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        implicitWidth: 132
                        implicitHeight: 42
                        radius: 12
                        color: parent.enabled ? (parent.hovered ? Theme.accent : Theme.primary) : "#27477D"
                    }
                }
            }
        }
    }

    Popup {
        id: helpPopup
        width: Math.min(680, window.width - 80)
        height: Math.min(570, window.height - 70)
        anchors.centerIn: Overlay.overlay
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        padding: 0
        background: Rectangle {
            radius: 20
            color: Theme.panelStrong
            border.width: 1
            border.color: Theme.borderStrong
        }
        contentItem: ColumnLayout {
            anchors.fill: parent
            anchors.margins: 26
            spacing: 14
            RowLayout {
                Layout.fillWidth: true
                Column {
                    Text {
                        text: "Команды JARVIS"
                        color: Theme.text
                        font.family: Theme.headingFont
                        font.pixelSize: 24
                        font.weight: Font.DemiBold
                    }
                    Text {
                        text: "Все действия доступны из строки на Главной"
                        color: Theme.muted
                        font.family: Theme.bodyFont
                        font.pixelSize: 13
                    }
                }
                Item { Layout.fillWidth: true }
                Button {
                    text: "×"
                    onClicked: helpPopup.close()
                    contentItem: Text {
                        text: parent.text
                        color: Theme.text
                        font.pixelSize: 22
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        implicitWidth: 40
                        implicitHeight: 40
                        radius: 12
                        color: parent.hovered ? "#263A68" : "#17284D"
                    }
                }
            }
            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 8
                model: [
                    ["chrome / открой VS Code", "Запустить приложение"],
                    ["/apps", "Открыть список установленных программ"],
                    ["1 … 5 / пресеты", "Быстрые запуски"],
                    ["VPN / Claude code", "Персональные команды запуска"],
                    ["заметки", "Открыть локальные заметки"],
                    ["/game preview", "Показать приложения для закрытия"],
                    ["/game / Протокол игры", "Включить игровой режим"],
                    ["kill chrome", "Завершить дерево процессов"],
                    ["выключить пк(30)", "Запланировать выключение"],
                    ["перезагрузка / спящий режим", "Управление питанием"],
                    ["/clear", "Очистить локальную историю"],
                    ["/exit", "Полностью завершить JARVIS"]
                ]
                delegate: Rectangle {
                    required property var modelData
                    width: ListView.view.width
                    height: 48
                    radius: 12
                    color: "#84101D3D"
                    border.width: 1
                    border.color: "#2E5B82BC"
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        Text {
                            Layout.preferredWidth: 220
                            text: modelData[0]
                            color: Theme.accent
                            font.family: Theme.monoFont
                            font.pixelSize: 11
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData[1]
                            color: Theme.text
                            font.family: Theme.bodyFont
                            font.pixelSize: 12
                        }
                    }
                }
            }
        }
    }

    // Native resize zones keep the custom frame resizable and preserve Windows snapping.
    MouseArea { z: 1000; anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom; width: 6; cursorShape: Qt.SizeHorCursor; onPressed: window.startSystemResize(Qt.LeftEdge) }
    MouseArea { z: 1000; anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom; width: 6; cursorShape: Qt.SizeHorCursor; onPressed: window.startSystemResize(Qt.RightEdge) }
    MouseArea { z: 1000; anchors.top: parent.top; anchors.left: parent.left; anchors.right: parent.right; height: 6; cursorShape: Qt.SizeVerCursor; onPressed: window.startSystemResize(Qt.TopEdge) }
    MouseArea { z: 1000; anchors.bottom: parent.bottom; anchors.left: parent.left; anchors.right: parent.right; height: 6; cursorShape: Qt.SizeVerCursor; onPressed: window.startSystemResize(Qt.BottomEdge) }

    Window {
        id: petWindow
        width: 128
        height: 128
        x: backend.petX
        y: backend.petY
        visible: backend.petVisible
        color: "transparent"
        flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        title: "JARVIS Pet"
        property string sprite: "idle"

        Image {
            id: petImage
            width: 128
            height: 128
            source: Qt.resolvedUrl("../assets/pet/" + petWindow.sprite + ".png")
            fillMode: Image.PreserveAspectFit
            smooth: false

            TapHandler {
                onTapped: {
                    petWindow.sprite = "emotion"
                    petRestore.restart()
                    backend.toggleMainWindow()
                }
            }

            DragHandler {
                id: petDrag
                target: null
                onActiveChanged: {
                    if (active) {
                        petWindow.sprite = "gesture"
                        petWindow.startSystemMove()
                    } else {
                        petWindow.sprite = "idle"
                        backend.savePetPosition(petWindow.x, petWindow.y)
                        petWindow.x = backend.petX
                        petWindow.y = backend.petY
                    }
                }
            }
        }

        Timer {
            id: petRestore
            interval: 520
            onTriggered: if (!petDrag.active) petWindow.sprite = "idle"
        }
        Timer {
            interval: 3000 + Math.random() * 4000
            repeat: true
            running: !backend.reducedMotion
            onTriggered: {
                if (!petDrag.active && petWindow.sprite === "idle") {
                    petWindow.sprite = "blink"
                    petRestore.interval = 150
                    petRestore.restart()
                }
                interval = 3000 + Math.random() * 4000
            }
        }
        Timer {
            interval: 20000 + Math.random() * 20000
            repeat: true
            running: !backend.reducedMotion
            onTriggered: {
                if (!petDrag.active && petWindow.sprite === "idle") {
                    const choices = ["laptop", "jump"]
                    petWindow.sprite = choices[Math.floor(Math.random() * choices.length)]
                    petRestore.interval = petWindow.sprite === "laptop" ? 4000 : 1200
                    petRestore.restart()
                }
                interval = 20000 + Math.random() * 20000
            }
        }
    }
}
