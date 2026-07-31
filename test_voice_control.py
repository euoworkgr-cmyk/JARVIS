from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from voice_control import (
    VoiceConfig,
    VoicePipeline,
    VoiceSetupError,
    confirmation_intent,
    normalize_transcript,
)


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

    @patch("voice_control.WhisperCppRecognizer")
    @patch("voice_control.SoundDeviceMicrophone", side_effect=VoiceSetupError("denied"))
    def test_denied_microphone_does_not_start_whisper(
        self, _microphone_mock, whisper_mock
    ) -> None:
        config = MagicMock(enabled=True)
        pipeline = VoicePipeline(
            config,
            on_status=MagicMock(),
            on_command=MagicMock(),
            on_confirm=MagicMock(),
            on_cancel=MagicMock(),
        )

        pipeline.run()

        whisper_mock.assert_not_called()
        self.assertEqual(pipeline.on_status.call_count, 1)

    def test_transient_voice_failures_use_bounded_backoff(self) -> None:
        config = MagicMock(enabled=True)
        statuses = MagicMock()
        pipeline = VoicePipeline(
            config,
            on_status=statuses,
            on_command=MagicMock(),
            on_confirm=MagicMock(),
            on_cancel=MagicMock(),
        )
        pipeline._run_once = MagicMock(side_effect=RuntimeError("busy"))
        pipeline._stop.wait = MagicMock(return_value=False)

        pipeline.run()

        self.assertEqual(
            [call.args[0] for call in pipeline._stop.wait.call_args_list],
            [4.0, 15.0, 60.0],
        )
        self.assertEqual(pipeline._run_once.call_count, 4)
        self.assertEqual(statuses.call_args.args[0], "disabled")

    def test_stop_cancels_active_recognizer(self) -> None:
        pipeline = VoicePipeline(
            MagicMock(enabled=True),
            on_status=MagicMock(),
            on_command=MagicMock(),
            on_confirm=MagicMock(),
            on_cancel=MagicMock(),
        )
        recognizer = MagicMock()
        pipeline._recognizer = recognizer

        pipeline.stop()

        recognizer.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
