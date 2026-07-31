from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import base64
import io
import json
import math
import os
from pathlib import Path
import queue
import re
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
import wave
from typing import Any, Callable

from PySide6.QtCore import QObject, Signal, Slot


SAMPLE_RATE = 16_000
WAKE_FRAME_SAMPLES = 1_280  # openWakeWord recommends multiples of 80 ms.
VAD_FRAME_SAMPLES = 512


class VoiceSetupError(RuntimeError):
    pass


@dataclass(frozen=True)
class VoiceConfig:
    enabled: bool
    wake_model: Path
    wake_melspec_model: Path
    wake_embedding_model: Path
    vad_model: Path
    whisper_executable: Path
    whisper_model: Path
    wake_threshold: float = 0.40
    vad_threshold: float = 0.50
    speech_start_timeout: float = 5.0
    silence_timeout: float = 0.75
    max_utterance_seconds: float = 12.0
    command_result_timeout: float = 30.0
    microphone_device: int | str | None = None

    @classmethod
    def from_environment(cls, resources: Path) -> "VoiceConfig":
        models = resources / "models"
        tools = resources / "tools"
        device_value = os.environ.get("JARVIS_MICROPHONE_DEVICE", "").strip()
        device: int | str | None = None
        if device_value:
            try:
                device = int(device_value)
            except ValueError:
                device = device_value
        return cls(
            enabled=os.environ.get("JARVIS_VOICE_ENABLED", "1").strip().casefold()
            not in {"0", "false", "no", "off"},
            wake_model=Path(
                os.environ.get(
                    "JARVIS_WAKE_MODEL",
                    models / "wakeword" / "jarvis.onnx",
                )
            ),
            wake_melspec_model=models / "wakeword" / "melspectrogram.onnx",
            wake_embedding_model=models / "wakeword" / "embedding_model.onnx",
            vad_model=Path(
                os.environ.get(
                    "JARVIS_VAD_MODEL",
                    models / "vad" / "silero_vad.onnx",
                )
            ),
            whisper_executable=Path(
                os.environ.get(
                    "JARVIS_WHISPER_EXECUTABLE",
                    tools / "whisper.cpp" / "Release" / "whisper-server.exe",
                )
            ),
            whisper_model=Path(
                os.environ.get(
                    "JARVIS_WHISPER_MODEL",
                    models / "whisper" / "ggml-small.bin",
                )
            ),
            wake_threshold=float(os.environ.get("JARVIS_WAKE_THRESHOLD", "0.40")),
            vad_threshold=float(os.environ.get("JARVIS_VAD_THRESHOLD", "0.50")),
            microphone_device=device,
        )

    def validate(self) -> None:
        missing = [
            (self.wake_model, "модель openWakeWord"),
            (self.wake_melspec_model, "openWakeWord melspectrogram"),
            (self.wake_embedding_model, "openWakeWord embedding"),
            (self.vad_model, "модель Silero VAD"),
            (self.whisper_executable, "whisper-cli.exe"),
            (self.whisper_model, "модель whisper.cpp"),
        ]
        absent = [f"{label}: {path}" for path, label in missing if not path.is_file()]
        if absent:
            raise VoiceSetupError("Не найдены локальные компоненты: " + "; ".join(absent))


class SoundDeviceMicrophone:
    def __init__(self, device: int | str | None = None) -> None:
        try:
            import numpy
            from scipy.signal import resample_poly
            import sounddevice
        except ImportError as error:
            raise VoiceSetupError(
                "Для микрофона установите зависимости из requirements-voice.txt"
            ) from error
        self._sounddevice = sounddevice
        self._numpy = numpy
        self._resample_poly = resample_poly
        selected_device = device
        if selected_device is None:
            selected_device = int(sounddevice.default.device[0])
        device_info = sounddevice.query_devices(selected_device, "input")
        self._native_rate = int(round(float(device_info["default_samplerate"])))
        self._native_frame_samples = int(round(self._native_rate * 0.08))
        self._stream = sounddevice.InputStream(
            samplerate=self._native_rate,
            blocksize=self._native_frame_samples,
            device=selected_device,
            channels=1,
            dtype="int16",
        )

    def __enter__(self) -> "SoundDeviceMicrophone":
        self._stream.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self._stream.stop()
        self._stream.close()

    def read(self) -> bytes:
        data, overflowed = self._stream.read(self._native_frame_samples)
        if overflowed:
            # A dropped frame is preferable to feeding stale audio to the models.
            return bytes(WAKE_FRAME_SAMPLES * 2)
        audio = self._numpy.asarray(data).reshape(-1)
        if self._native_rate != SAMPLE_RATE:
            divisor = math.gcd(self._native_rate, SAMPLE_RATE)
            audio = self._resample_poly(
                audio.astype("float32"),
                SAMPLE_RATE // divisor,
                self._native_rate // divisor,
            )
            audio = self._numpy.clip(self._numpy.rint(audio), -32768, 32767).astype(
                self._numpy.int16
            )
        if audio.size < WAKE_FRAME_SAMPLES:
            audio = self._numpy.pad(audio, (0, WAKE_FRAME_SAMPLES - audio.size))
        return audio[:WAKE_FRAME_SAMPLES].astype(self._numpy.int16, copy=False).tobytes()

    def flush(self) -> None:
        """Drop buffered speaker/beep echo before listening for the user again."""
        self._stream.stop()
        self._stream.start()


class OpenWakeWordDetector:
    def __init__(
        self,
        model_path: Path,
        melspec_model_path: Path,
        embedding_model_path: Path,
        threshold: float,
    ) -> None:
        try:
            import numpy
            from openwakeword.model import Model
        except ImportError as error:
            raise VoiceSetupError(
                "Для wake word установите зависимости из requirements-voice.txt"
            ) from error
        self._numpy = numpy
        self._threshold = threshold
        self._model = Model(
            wakeword_models=[str(model_path)],
            inference_framework="onnx",
            melspec_model_path=str(melspec_model_path),
            embedding_model_path=str(embedding_model_path),
        )

    def detected(self, pcm: bytes) -> bool:
        audio = self._numpy.frombuffer(pcm, dtype=self._numpy.int16)
        scores = self._model.predict(audio)
        return max((float(value) for value in scores.values()), default=0.0) >= self._threshold

    def reset(self) -> None:
        reset = getattr(self._model, "reset", None)
        if callable(reset):
            reset()


class SileroVoiceActivityDetector:
    """Minimal streaming Silero ONNX wrapper without the heavyweight PyTorch runtime."""

    def __init__(self, model_path: Path, threshold: float) -> None:
        try:
            import numpy
            import onnxruntime
        except ImportError as error:
            raise VoiceSetupError(
                "Для VAD установите зависимости из requirements-voice.txt"
            ) from error
        self._numpy = numpy
        self._threshold = threshold
        options = onnxruntime.SessionOptions()
        options.inter_op_num_threads = 1
        options.intra_op_num_threads = 1
        self._session = onnxruntime.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"], sess_options=options
        )
        self.reset()

    def is_speech(self, pcm: bytes) -> bool:
        audio = self._numpy.frombuffer(pcm, dtype=self._numpy.int16).astype("float32")
        audio = (audio / 32768.0).reshape(1, -1)
        combined = self._numpy.concatenate((self._context, audio), axis=1)
        output, self._state = self._session.run(
            None,
            {
                "input": combined,
                "state": self._state,
                "sr": self._numpy.array(SAMPLE_RATE, dtype="int64"),
            },
        )
        self._context = combined[:, -64:]
        return float(output.reshape(-1)[0]) >= self._threshold

    def reset(self) -> None:
        self._state = self._numpy.zeros((2, 1, 128), dtype="float32")
        self._context = self._numpy.zeros((1, 64), dtype="float32")


class WhisperCppRecognizer:
    COMMAND_PROMPT = (
        "Команды голосового ассистента Supersonic (фраза пробуждения Джарвис): "
        "открой, запусти, закрой, заверши, выключи ПК, "
        "Яндекс Браузер, Яндекс Музыка, Telegram, VS Code, ChatGPT, VPN, "
        "подтверждаю, отмена."
    )

    def __init__(self, executable: Path, model: Path) -> None:
        self._executable = executable
        self._model = model
        self._port = self._available_port()
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self._process = subprocess.Popen(
            [
                str(executable),
                "-m",
                str(model),
                "-l",
                "ru",
                "-nt",
                "-sns",
                "-t",
                str(min(6, os.cpu_count() or 4)),
                "-bs",
                "5",
                "--prompt",
                self.COMMAND_PROMPT,
                "--host",
                "127.0.0.1",
                "--port",
                str(self._port),
            ],
            cwd=str(executable.parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        self._wait_until_ready()

    @staticmethod
    def _available_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            return int(listener.getsockname()[1])

    def _wait_until_ready(self) -> None:
        deadline = time.monotonic() + 60
        url = f"http://127.0.0.1:{self._port}/"
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise RuntimeError("whisper-server завершился при загрузке модели")
            try:
                with urllib.request.urlopen(url, timeout=0.4) as response:
                    if response.status == 200:
                        return
            except (OSError, urllib.error.URLError):
                time.sleep(0.1)
        self.close()
        raise TimeoutError("whisper-server не загрузил модель за 60 секунд")

    def recognize(self, pcm: bytes) -> str:
        audio = io.BytesIO()
        with wave.open(audio, "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(SAMPLE_RATE)
            stream.writeframes(pcm)
        boundary = f"jarvis-{time.time_ns()}"
        body = self._multipart_body(boundary, audio.getvalue())
        request = urllib.request.Request(
            f"http://127.0.0.1:{self._port}/inference",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError, urllib.error.URLError) as error:
            raise RuntimeError(f"whisper.cpp не распознал команду: {error}") from error
        return normalize_transcript(str(result.get("text", "")))

    @staticmethod
    def _multipart_body(boundary: str, wav: bytes) -> bytes:
        marker = boundary.encode("ascii")
        parts = [
            b"--" + marker + b"\r\nContent-Disposition: form-data; name=\"file\"; filename=\"command.wav\"\r\nContent-Type: audio/wav\r\n\r\n" + wav + b"\r\n",
            b"--" + marker + b"\r\nContent-Disposition: form-data; name=\"response_format\"\r\n\r\njson\r\n",
            b"--" + marker + b"\r\nContent-Disposition: form-data; name=\"temperature\"\r\n\r\n0.0\r\n",
            b"--" + marker + b"\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\nru\r\n",
            b"--" + marker + b"\r\nContent-Disposition: form-data; name=\"prompt\"\r\n\r\n" + WhisperCppRecognizer.COMMAND_PROMPT.encode("utf-8") + b"\r\n",
            b"--" + marker + b"--\r\n",
        ]
        return b"".join(parts)

    def close(self) -> None:
        if self._process.poll() is not None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=2)


class LocalSpeaker:
    """Offline TTS through the Russian Windows SAPI voice installed on the PC."""

    def say(self, text: str) -> None:
        value = text.strip()
        if not value or os.name != "nt":
            return
        escaped = value.replace("'", "''")
        script = (
            "$s=New-Object -ComObject SAPI.SpVoice; "
            "$ru=$s.GetVoices() | Where-Object { $_.GetDescription() -match 'Russian|Irina' } | Select-Object -First 1; "
            "if($ru){$s.Voice=$ru}; "
            f"$s.Speak('{escaped}') | Out-Null; "
            "[System.Runtime.InteropServices.Marshal]::ReleaseComObject($s) | Out-Null"
        )
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                encoded,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    @staticmethod
    def wake_signal() -> None:
        if os.name == "nt":
            import winsound

            winsound.MessageBeep(winsound.MB_OK)


def normalize_transcript(value: str) -> str:
    text = " ".join(value.replace("[BLANK_AUDIO]", "").split()).strip(" .,!?:;—-")
    return re.sub(r"^(?:эй\s+)?джарвис[,.!?\s-]*", "", text, flags=re.IGNORECASE).strip()


def confirmation_intent(value: str) -> bool | None:
    normalized = re.sub(r"[^а-яёa-z]+", " ", value.casefold()).strip()
    if any(word in normalized.split() for word in ("подтверждаю", "подтвердить", "да", "выполняй")):
        return True
    if any(word in normalized.split() for word in ("отмена", "отменить", "нет", "стоп")):
        return False
    return None


class VoicePipeline:
    RETRY_DELAYS = (4.0, 15.0, 60.0)

    def __init__(
        self,
        config: VoiceConfig,
        *,
        on_status: Callable[[str, str], None],
        on_command: Callable[[str], None],
        on_confirm: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self.config = config
        self.on_status = on_status
        self.on_command = on_command
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self._stop = threading.Event()
        self._accept_outcomes = threading.Event()
        self._outcomes: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=2)
        self._recognizer: WhisperCppRecognizer | None = None
        self._recognizer_lock = threading.Lock()

    def stop(self) -> None:
        self._stop.set()
        with self._recognizer_lock:
            if self._recognizer is not None:
                self._recognizer.close()

    def submit_outcome(self, outcome: dict[str, Any]) -> None:
        if not self._accept_outcomes.is_set():
            return
        try:
            self._outcomes.put_nowait(dict(outcome))
        except queue.Full:
            try:
                self._outcomes.get_nowait()
            except queue.Empty:
                pass
            self._outcomes.put_nowait(dict(outcome))

    def run(self) -> None:
        if not self.config.enabled:
            self.on_status("disabled", "Голосовое управление отключено")
            return
        try:
            self.config.validate()
        except Exception as error:
            self.on_status("error", str(error))
            return
        for attempt in range(len(self.RETRY_DELAYS) + 1):
            if self._stop.is_set():
                return
            try:
                self._run_once()
                return
            except VoiceSetupError as error:
                self.on_status("error", str(error))
                return
            except Exception as error:
                self.on_status("error", str(error))
                if attempt >= len(self.RETRY_DELAYS):
                    self.on_status(
                        "disabled",
                        "Голосовое управление остановлено. Запустите повтор вручную.",
                    )
                    return
                if self._stop.wait(self.RETRY_DELAYS[attempt]):
                    return
                self.on_status("restarting", "Переподключаю голосовое управление")

    def _run_once(self) -> None:
        with SoundDeviceMicrophone(self.config.microphone_device) as microphone:
            recognizer: WhisperCppRecognizer | None = None
            try:
                try:
                    wake = OpenWakeWordDetector(
                        self.config.wake_model,
                        self.config.wake_melspec_model,
                        self.config.wake_embedding_model,
                        self.config.wake_threshold,
                    )
                    vad = SileroVoiceActivityDetector(
                        self.config.vad_model, self.config.vad_threshold
                    )
                    speaker = LocalSpeaker()
                    recognizer = WhisperCppRecognizer(
                        self.config.whisper_executable, self.config.whisper_model
                    )
                except VoiceSetupError:
                    raise
                except Exception as error:
                    raise VoiceSetupError(str(error)) from error
                with self._recognizer_lock:
                    self._recognizer = recognizer
                self._run_loop(microphone, wake, vad, recognizer, speaker)
            finally:
                with self._recognizer_lock:
                    if self._recognizer is recognizer:
                        self._recognizer = None
                if recognizer is not None:
                    recognizer.close()

    def _run_loop(
        self,
        microphone: SoundDeviceMicrophone,
        wake: OpenWakeWordDetector,
        vad: SileroVoiceActivityDetector,
        recognizer: WhisperCppRecognizer,
        speaker: LocalSpeaker,
    ) -> None:
        self.on_status("sleeping", "Ожидаю слово «Джарвис»")
        while not self._stop.is_set():
            frame = microphone.read()
            if not wake.detected(frame):
                continue
            self.on_status("awake", "Слушаю")
            speaker.wake_signal()
            microphone.flush()
            command = self._capture_and_recognize(microphone, vad, recognizer)
            wake.reset()
            if not command:
                speaker.say("Не расслышал команду")
                self.on_status("sleeping", "Ожидаю слово «Джарвис»")
                continue
            self._accept_outcomes.set()
            self.on_command(command)
            outcome = self._wait_for_outcome()
            if outcome is not None:
                self._handle_outcome(outcome, microphone, vad, recognizer, speaker)
            self.on_status("sleeping", "Ожидаю слово «Джарвис»")

    def _capture_and_recognize(
        self,
        microphone: SoundDeviceMicrophone,
        vad: SileroVoiceActivityDetector,
        recognizer: WhisperCppRecognizer,
    ) -> str:
        self.on_status("listening", "Говорите")
        pcm = self._capture_utterance(microphone, vad)
        if not pcm:
            return ""
        self.on_status("recognizing", "Распознаю команду")
        return recognizer.recognize(pcm)

    def _capture_utterance(
        self, microphone: SoundDeviceMicrophone, vad: SileroVoiceActivityDetector
    ) -> bytes:
        vad.reset()
        started = False
        started_at = time.monotonic()
        speech_started_at = started_at
        last_speech = started_at
        frames: list[bytes] = []
        pre_roll: deque[bytes] = deque(maxlen=5)
        while not self._stop.is_set():
            frame = microphone.read()
            now = time.monotonic()
            decisions = [
                vad.is_speech(frame[offset : offset + VAD_FRAME_SAMPLES * 2])
                for offset in range(0, len(frame) - VAD_FRAME_SAMPLES * 2 + 1, VAD_FRAME_SAMPLES * 2)
            ]
            speech = any(decisions)
            if not started:
                pre_roll.append(frame)
                if speech:
                    started = True
                    speech_started_at = now
                    last_speech = now
                    frames.extend(pre_roll)
                elif now - started_at >= self.config.speech_start_timeout:
                    return b""
                continue
            frames.append(frame)
            if speech:
                last_speech = now
            if started:
                if now - last_speech >= self.config.silence_timeout:
                    break
                if now - speech_started_at >= self.config.max_utterance_seconds:
                    break
        return b"".join(frames)

    def _wait_for_outcome(self) -> dict[str, Any] | None:
        self.on_status("executing", "Выполняю команду")
        try:
            outcome = self._outcomes.get(timeout=self.config.command_result_timeout)
            self._accept_outcomes.clear()
            return outcome
        except queue.Empty:
            self._accept_outcomes.clear()
            self.on_status("error", "Команда не завершилась вовремя")
            return None

    def _handle_outcome(
        self,
        outcome: dict[str, Any],
        microphone: SoundDeviceMicrophone,
        vad: SileroVoiceActivityDetector,
        recognizer: WhisperCppRecognizer,
        speaker: LocalSpeaker,
    ) -> None:
        if outcome.get("status") != "pending":
            speaker.say(str(outcome.get("title") or outcome.get("detail") or "Готово"))
            microphone.flush()
            return
        speaker.say(
            f"{outcome.get('title', 'Требуется подтверждение')}. "
            "Скажите подтверждаю или отмена"
        )
        microphone.flush()
        answer = self._capture_and_recognize(microphone, vad, recognizer)
        intent = confirmation_intent(answer)
        if intent is True:
            self._accept_outcomes.set()
            self.on_confirm()
            final = self._wait_for_outcome()
            if final:
                speaker.say(str(final.get("title") or "Готово"))
                microphone.flush()
        else:
            self._accept_outcomes.set()
            self.on_cancel()
            final = self._wait_for_outcome()
            if final:
                speaker.say(str(final.get("title") or "Действие отменено"))
                microphone.flush()


class LocalVoiceController(QObject):
    statusChanged = Signal(str, str)
    commandRecognized = Signal(str)
    confirmationRequested = Signal()
    cancellationRequested = Signal()

    def __init__(self, config: VoiceConfig, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._pipeline = VoicePipeline(
            config,
            on_status=self.statusChanged.emit,
            on_command=self.commandRecognized.emit,
            on_confirm=self.confirmationRequested.emit,
            on_cancel=self.cancellationRequested.emit,
        )
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._pipeline.run, name="jarvis-local-voice", daemon=True
        )
        self._thread.start()

    @Slot(object)
    def submitOutcome(self, outcome: object) -> None:
        if isinstance(outcome, dict):
            self._pipeline.submit_outcome(outcome)

    def stop(self, timeout: float = 2.0) -> None:
        self._pipeline.stop()
        if self._thread:
            self._thread.join(timeout)
