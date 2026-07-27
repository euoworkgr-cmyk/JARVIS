import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "."
import ".." as Shared

ApplicationWindow {
    id: window
    width: 1180
    height: 760
    minimumWidth: 1000
    minimumHeight: 680
    visible: false
    color: PersonalTheme.backgroundDeep
    flags: Qt.Window | Qt.FramelessWindowHint
    title: "Supersonic"
    property bool windowMoving: false

    function pageComponent(page) {
        if (page === "statistics")
            return statisticsPageComponent
        if (page === "customization")
            return customizationPageComponent
        if (page === "settings")
            return settingsPageComponent
        return homePageComponent
    }

    function showPage(page) {
        const component = pageComponent(page)
        if (pageStack.currentItem && pageStack.currentItem.pageKey === page)
            return
        pageStack.replace(
            pageStack.currentItem,
            component,
            {},
            StackView.PushTransition
        )
    }

    Component.onCompleted: Shared.Theme.reducedMotion = backend.reducedMotion

    onClosing: function(close) {
        if (!backend.quitting) {
            close.accepted = false
            window.hide()
        }
    }

    Connections {
        target: backend
        function onHelpRequested() { backend.setPage("settings") }
        function onCurrentPageChanged() { window.showPage(backend.currentPage) }
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
                    spacing: -1
                    Shared.LabelSharp {
                        text: "Supersonic"
                        color: PersonalTheme.text
                        font.family: PersonalTheme.displayFont
                        font.pixelSize: PersonalTheme.body
                        font.weight: Font.DemiBold
                    }
                    Shared.LabelSharp {
                        text: "Голосовой помощник"
                        color: PersonalTheme.subtle
                        font.family: PersonalTheme.utilityFont
                        font.pixelSize: PersonalTheme.micro
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
                        { label: "Свернуть", action: "minimize" },
                        { label: "Развернуть", action: "maximize" },
                        { label: "Скрыть в трей", action: "close" }
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
                        PersonalIcon {
                            anchors.centerIn: parent
                            width: 18
                            height: 18
                            name: modelData.action
                            color: PersonalTheme.muted
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

        Component {
            id: homePageComponent
            PersonalHomePage { property string pageKey: "home" }
        }
        Component {
            id: statisticsPageComponent
            PersonalStatisticsPage { property string pageKey: "statistics" }
        }
        Component {
            id: customizationPageComponent
            PersonalPlaceholderPage {
                property string pageKey: "customization"
                pageTitle: "Кастомизация"
                pageDescription: "Здесь появятся темы, фоновые рисунки и параметры визуального поведения. Структура personal-версии уже отделена от палитры, поэтому новые темы не потребуют переделки экранов."
                symbol: "◌"
            }
        }
        Component {
            id: settingsPageComponent
            PersonalSettingsPage { property string pageKey: "settings" }
        }

        StackView {
            id: pageStack
            anchors.left: sidebar.right
            anchors.right: parent.right
            anchors.top: titleBar.bottom
            anchors.bottom: parent.bottom
            anchors.leftMargin: 30
            anchors.rightMargin: 30
            anchors.topMargin: 20
            anchors.bottomMargin: 20
            initialItem: homePageComponent
            clip: true

            pushEnter: Transition {
                ParallelAnimation {
                    NumberAnimation {
                        property: "opacity"
                        from: 0
                        to: 1
                        duration: PersonalTheme.durSlow
                        easing.type: PersonalTheme.easeOut
                    }
                    NumberAnimation {
                        property: "y"
                        from: 12
                        to: 0
                        duration: PersonalTheme.durSlow
                        easing.type: PersonalTheme.easeOut
                    }
                }
            }
            pushExit: Transition {
                ParallelAnimation {
                    NumberAnimation {
                        property: "opacity"
                        from: 1
                        to: 0
                        duration: PersonalTheme.durSlow
                        easing.type: PersonalTheme.easeOut
                    }
                    NumberAnimation {
                        property: "y"
                        from: 0
                        to: -12
                        duration: PersonalTheme.durSlow
                        easing.type: PersonalTheme.easeOut
                    }
                }
            }
        }
    }

    Rectangle {
        id: toast
        z: 900
        width: Math.round(Math.min(420, window.width - 80))
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
            NumberAnimation { duration: PersonalTheme.durFocus; easing.type: PersonalTheme.easeOut }
        }

        Column {
            anchors.left: parent.left
            anchors.leftMargin: 18
            anchors.right: closeToast.left
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            spacing: 4
            Shared.LabelSharp {
                width: parent.width
                text: backend.lastMessage.title || ""
                color: PersonalTheme.text
                elide: Text.ElideRight
                font.family: PersonalTheme.bodyFont
                font.pixelSize: PersonalTheme.label
                font.weight: Font.DemiBold
            }
            Shared.LabelSharp {
                width: parent.width
                visible: text.length > 0
                text: backend.lastMessage.detail || ""
                color: PersonalTheme.muted
                elide: Text.ElideRight
                font.family: PersonalTheme.bodyFont
                font.pixelSize: PersonalTheme.micro
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
            Shared.LabelSmooth {
                anchors.centerIn: parent
                text: "×"
                color: PersonalTheme.muted
                font.pixelSize: PersonalTheme.title
            }
            HoverHandler { id: closeToastHover }
            TapHandler { onTapped: backend.dismissMessage() }
        }
    }

    Popup {
        id: confirmPopup
        width: Math.round(Math.min(510, window.width - 80))
        height: Math.round(Math.min(420, Math.max(254, confirmContent.implicitHeight + 42)))
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

            Shared.LabelSmooth {
                Layout.fillWidth: true
                text: backend.pendingAction.title || "Подтвердите действие"
                color: PersonalTheme.text
                wrapMode: Text.WordWrap
                font.family: PersonalTheme.displayFont
                font.pixelSize: PersonalTheme.hero
            }
            Shared.LabelSharp {
                Layout.fillWidth: true
                text: backend.pendingAction.detail || ""
                color: PersonalTheme.muted
                wrapMode: Text.WordWrap
                font.family: PersonalTheme.bodyFont
                font.pixelSize: PersonalTheme.label
            }

            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: Boolean(backend.pendingAction.candidates
                                 && backend.pendingAction.candidates.length > 0)
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
                        Shared.LabelSharp {
                            text: modelData.name
                            color: PersonalTheme.text
                            font.family: PersonalTheme.bodyFont
                            font.pixelSize: PersonalTheme.caption
                        }
                        Item { Layout.fillWidth: true }
                        Shared.LabelSharp {
                            text: "PID " + modelData.pid
                            color: PersonalTheme.subtle
                            font.family: PersonalTheme.utilityFont
                            font.pixelSize: PersonalTheme.micro
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
                    contentItem: Shared.LabelSharp {
                        text: parent.text
                        color: PersonalTheme.text
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: PersonalTheme.label
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
                    contentItem: Shared.LabelSharp {
                        text: parent.text
                        color: PersonalTheme.backgroundDeep
                        font.family: PersonalTheme.bodyFont
                        font.pixelSize: PersonalTheme.label
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
