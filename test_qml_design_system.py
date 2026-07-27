from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent
QML_ROOT = ROOT / "qml"
TYPE_ROLES = {"hero", "title", "body", "label", "caption", "micro"}


def qml_sources() -> dict[Path, str]:
    return {
        path: path.read_text(encoding="utf-8")
        for path in QML_ROOT.rglob("*.qml")
    }


def blocks(source: str, component: str) -> list[str]:
    result: list[str] = []
    pattern = re.compile(rf"\b{re.escape(component)}\s*\{{")
    for match in pattern.finditer(source):
        depth = 0
        end = match.start()
        for end in range(match.start(), len(source)):
            if source[end] == "{":
                depth += 1
            elif source[end] == "}":
                depth -= 1
                if depth == 0:
                    result.append(source[match.start() : end + 1])
                    break
    return result


class QmlDesignSystemTests(unittest.TestCase):
    def test_only_six_pixel_size_roles_are_used(self) -> None:
        forbidden_size_property = "font." + "point" + "Size"
        for path, source in qml_sources().items():
            self.assertNotIn(forbidden_size_property, source, path)
            for value in re.findall(r"font\.pixelSize:\s*([^\r\n]+)", source):
                normalized = value.strip().rstrip("}").strip()
                match = re.fullmatch(r"(?:Theme|PersonalTheme)\.(\w+)", normalized)
                self.assertIsNotNone(match, f"{path}: unsupported font size {value}")
                self.assertIn(match.group(1), TYPE_ROLES, path)

        theme = (QML_ROOT / "Theme.qml").read_text(encoding="utf-8")
        expected = {
            "hero": 26,
            "title": 15,
            "body": 13,
            "label": 12,
            "caption": 11,
            "micro": 10,
        }
        for role, size in expected.items():
            self.assertIn(f"readonly property int {role}: {size}", theme)

    def test_text_rendering_uses_reusable_hybrid_components(self) -> None:
        sources = qml_sources()
        raw_text_paths = [
            path
            for path, source in sources.items()
            if path.name not in {"LabelSharp.qml", "LabelSmooth.qml"}
            and re.search(r"\bText\s*\{", source)
        ]
        self.assertEqual(raw_text_paths, [])

        sharp = (QML_ROOT / "LabelSharp.qml").read_text(encoding="utf-8")
        smooth = (QML_ROOT / "LabelSmooth.qml").read_text(encoding="utf-8")
        self.assertIn("renderType: Text.NativeRendering", sharp)
        self.assertIn("renderType: Text.QtRendering", smooth)

        for path, source in sources.items():
            for block in blocks(source, "LabelSharp"):
                self.assertNotRegex(
                    block,
                    r"font\.pixelSize:\s*(?:Theme|PersonalTheme)\.(?:hero|title)",
                    f"{path}: large text must use LabelSmooth",
                )
            for component in ("TextField", "TextArea"):
                for block in blocks(source, component):
                    self.assertIn("renderType: Text.", block, f"{path}: {component}")

    def test_computed_item_geometry_is_pixel_aligned(self) -> None:
        property_pattern = re.compile(r"^\s*(?:x|y|width|height):\s*(.+)$", re.MULTILINE)
        for path, source in qml_sources().items():
            for expression in property_pattern.findall(source):
                expression = expression.strip()
                computed = "Math." in expression or "*" in expression or "/" in expression
                if computed:
                    self.assertTrue(
                        expression.startswith("Math.round("),
                        f"{path}: computed geometry is not rounded: {expression}",
                    )

    def test_shared_motion_and_stack_transitions_are_present(self) -> None:
        theme = (QML_ROOT / "Theme.qml").read_text(encoding="utf-8")
        for declaration in (
            "durFast: reducedMotion ? 0 : 130",
            "durBase: reducedMotion ? 0 : 200",
            "durSlow: reducedMotion ? 0 : 260",
            "easeOut: Easing.OutCubic",
            "property bool reducedMotion: false",
        ):
            self.assertIn(declaration, theme)

        for relative in (Path("Main.qml"), Path("personal/PersonalMain.qml")):
            source = (QML_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("StackView {", source)
            self.assertIn("pushEnter: Transition", source)
            self.assertIn("pushExit: Transition", source)
            self.assertNotIn("StackLayout {", source)

        home = (QML_ROOT / "personal" / "PersonalHomePage.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("presetTap.pressed ? 0.97", home)
        self.assertIn("protocolTap.pressed ? 0.97", home)
        self.assertIn("historyTap.pressed ? 0.97", home)
        self.assertIn("index * PersonalTheme.staggerStep", home)
        self.assertIn("PersonalTheme.durPulse / 2", home)

        statistics = (
            QML_ROOT / "personal" / "PersonalStatisticsPage.qml"
        ).read_text(encoding="utf-8")
        self.assertGreaterEqual(statistics.count("duration: PersonalTheme.durProgress"), 2)

        settings = (QML_ROOT / "personal" / "PersonalSettingsPage.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("onToggled: Shared.Theme.reducedMotion = checked", settings)

    def test_high_dpi_policy_precedes_application_creation(self) -> None:
        source = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        policy = source.index("setHighDpiScaleFactorRoundingPolicy")
        creation = source.index("app = QApplication(sys.argv)")
        self.assertLess(policy, creation)
        self.assertIn("HighDpiScaleFactorRoundingPolicy.PassThrough", source)


if __name__ == "__main__":
    unittest.main()
