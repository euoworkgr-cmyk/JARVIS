$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$wakeDirectory = Join-Path $projectRoot "models\wakeword"
$vadDirectory = Join-Path $projectRoot "models\vad"
$whisperDirectory = Join-Path $projectRoot "models\whisper"
$toolDirectory = Join-Path $projectRoot "tools\whisper.cpp"

New-Item -ItemType Directory -Force -Path $wakeDirectory, $vadDirectory, $whisperDirectory, $toolDirectory | Out-Null

function Get-LocalFile {
    param([string]$Url, [string]$Target)
    if (-not (Test-Path -LiteralPath $Target)) {
        Write-Host "Downloading $(Split-Path -Leaf $Target)..."
        Invoke-WebRequest -Uri $Url -OutFile $Target
    }
}

Get-LocalFile "https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/hey_jarvis_v0.1.onnx" (Join-Path $wakeDirectory "jarvis.onnx")
Get-LocalFile "https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/melspectrogram.onnx" (Join-Path $wakeDirectory "melspectrogram.onnx")
Get-LocalFile "https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/embedding_model.onnx" (Join-Path $wakeDirectory "embedding_model.onnx")
Get-LocalFile "https://raw.githubusercontent.com/snakers4/silero-vad/master/src/silero_vad/data/silero_vad.onnx" (Join-Path $vadDirectory "silero_vad.onnx")

$whisperArchive = Join-Path $toolDirectory "whisper-bin-x64.zip"
Get-LocalFile "https://github.com/ggml-org/whisper.cpp/releases/download/v1.9.1/whisper-bin-x64.zip" $whisperArchive
$expectedArchiveHash = "7D8BE46ECD31828E1EB7A2ECDD0D6B314FEAFD82163038AB6092594B0A063539"
if ((Get-FileHash -LiteralPath $whisperArchive -Algorithm SHA256).Hash -ne $expectedArchiveHash) {
    throw "whisper.cpp archive checksum mismatch"
}
if (-not (Test-Path -LiteralPath (Join-Path $toolDirectory "Release\whisper-server.exe"))) {
    Expand-Archive -LiteralPath $whisperArchive -DestinationPath $toolDirectory -Force
}

$whisperModel = Join-Path $whisperDirectory "ggml-base.bin"
Get-LocalFile "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin?download=true" $whisperModel
$expectedModelHash = "465707469FF3A37A2B9B8D8F89F2F99DE7299DAC"
if ((Get-FileHash -LiteralPath $whisperModel -Algorithm SHA1).Hash -ne $expectedModelHash) {
    throw "Whisper base model checksum mismatch"
}

Write-Host "Local voice models are ready."
