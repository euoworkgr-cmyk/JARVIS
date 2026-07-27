import QtQuick
import QtQuick.Window

Window {
    id: petWindow
    objectName: "petWindow"
    width: 128
    height: 128
    x: backend.petX
    y: backend.petY
    visible: backend.petVisible
    color: "transparent"
    transientParent: null
    flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    title: "JARVIS Pet"
    property string sprite: "idle"

    Image {
        width: 128
        height: 128
        source: Qt.resolvedUrl("../assets/pet/" + petWindow.sprite + ".png")
        fillMode: Image.PreserveAspectFit
        smooth: false

        TapHandler {
            onTapped: {
                petWindow.sprite = "emotion"
                petRestore.restart()
                backend.showMainWindow()
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
