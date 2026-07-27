from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from voice_control import VoiceConfig, VoiceSetupError, confirmation_intent, normalize_transcript


class VoiceControlTests(unittest.TestCase):
    def test_transcript_is_cleaned_before_command_parsing(self) -> None:
        self.assertEqual(normalize_transcript("  Джарвис, открой VS Code.  "), "открой VS Code")
        self.assertEqual(normalize_transcript("[BLANK_AUDIO]"), "")

    def test_confirmation_vocabulary_is_deliberately_small(self) -> None:
        self.assertIs(confirmation_intent("Да, подтверждаю"), True)
        self.assertIs(confirmation_intent("нет, отмена"), False)
        self.assertIsNone(confirmation_intent("открой браузер"))

    def test_configuration_fails_closed_without_local_models(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = VoiceConfig(
                enabled=True,
                wake_model=root / "jarvis.onnx",
                wake_melspec_model=root / "melspectrogram.onnx",
                wake_embedding_model=root / "embedding_model.onnx",
                vad_model=root / "silero_vad.onnx",
                whisper_executable=root / "whisper-cli.exe",
                whisper_model=root / "ggml-small.bin",
            )
            with self.assertRaises(VoiceSetupError):
                config.validate()

    def test_default_configuration_uses_multilingual_small_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = VoiceConfig.from_environment(Path(directory))

        self.assertEqual(config.whisper_model.name, "ggml-small.bin")
        self.assertLess(config.wake_threshold, 0.5)


if __name__ == "__main__":
    unittest.main()
