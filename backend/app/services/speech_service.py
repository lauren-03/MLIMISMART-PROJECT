"""Reads advice aloud: Kasanoma (Piper) for Chichewa, Meta MMS for English."""
import hashlib
import io
import logging
import re
import threading
import wave
from collections import OrderedDict
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from ..config import settings

log = logging.getLogger(__name__)

# Free for non-commercial use (CC-BY-NC 4.0).
MODELS = {"NY": "facebook/mms-tts-nya", "EN": "facebook/mms-tts-eng"}
# Chichewa Piper voice, kept in backend/voices (not in Git).
KASANOMA = Path(__file__).resolve().parents[2] / "voices" / "kasanoma-chichewa" / "model.onnx"
MAX_CHARS = 1200
CACHE_SIZE = 200

_loaded: dict[str, tuple] = {}
_lock = threading.Lock()
_cache: "OrderedDict[str, bytes]" = OrderedDict()
# One worker, so voice generation never competes with itself for the CPU.
_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="voice")
_pending: dict[str, Future] = {}
_pending_lock = threading.Lock()


def _has_mms() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        return False
    return True


def _use_kasanoma(language: str) -> bool:
    if language != "NY" or settings.chichewa_voice != "kasanoma" or not KASANOMA.exists():
        return False
    try:
        import piper  # noqa: F401
    except ImportError:
        return False
    return True


def available() -> bool:
    return _has_mms() or _use_kasanoma("NY")


def voice_name(language: str) -> str:
    return "Kasanoma (Piper)" if _use_kasanoma(language) else MODELS[language]


def _piper():
    with _lock:
        if "piper" not in _loaded:
            from piper import PiperVoice

            log.info("Loading voice %s", KASANOMA.parent.name)
            _loaded["piper"] = PiperVoice.load(str(KASANOMA))
        return _loaded["piper"]


def _model(language: str):
    with _lock:
        if language not in _loaded:
            from transformers import AutoTokenizer, VitsModel

            name = MODELS[language]
            log.info("Loading voice %s", name)
            model = VitsModel.from_pretrained(name)
            model.eval()
            _loaded[language] = (model, AutoTokenizer.from_pretrained(name))
        return _loaded[language]


EN_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
           "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
           "eighteen", "nineteen"]
EN_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
NY_ONES = ["ziro", "chimodzi", "ziwiri", "zitatu", "zinayi", "zisanu", "zisanu ndi chimodzi",
           "zisanu ndi ziwiri", "zisanu ndi zitatu", "zisanu ndi zinayi"]
NY_TENS = ["", "khumi", "makumi awiri", "makumi atatu", "makumi anayi", "makumi asanu",
           "makumi asanu ndi limodzi", "makumi asanu ndi awiri", "makumi asanu ndi atatu",
           "makumi asanu ndi anayi"]
NY_HUNDREDS = ["", "zana limodzi", "mazana awiri", "mazana atatu", "mazana anayi", "mazana asanu",
               "mazana asanu ndi limodzi", "mazana asanu ndi awiri", "mazana asanu ndi atatu",
               "mazana asanu ndi anayi"]


def _number_words(n: int, language: str) -> str:
    if n >= 1000:
        return str(n)
    if language == "NY":
        parts = []
        if n >= 100:
            parts.append(NY_HUNDREDS[n // 100])
            n %= 100
        if n >= 10:
            parts.append(NY_TENS[n // 10])
            n %= 10
        if n or not parts:
            parts.append(NY_ONES[n])
        return " ndi ".join(parts)
    words = []
    if n >= 100:
        words.append(f"{EN_ONES[n // 100]} hundred")
        n %= 100
        if n:
            words.append("and")
    if n >= 20:
        words.append(EN_TENS[n // 10] + (f" {EN_ONES[n % 10]}" if n % 10 else ""))
    elif n or not words:
        words.append(EN_ONES[n])
    return " ".join(words)


def _sentences(text: str, language: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()[:MAX_CHARS]
    # Symbols the voices cannot read.
    words = {"NY": (" peresenti", " digiri", " milimita"), "EN": (" percent", " degrees", " millimetres")}
    percent, degrees, mm = words[language]
    text = text.replace("%", percent).replace("°C", degrees)
    text = re.sub(r"(\d)\s?C\b", r"\1" + degrees, text)
    text = re.sub(r"(\d)\s?mm\b", r"\1" + mm, text)
    # Decimals are rounded; the voices have no letters for digits.
    text = re.sub(r"\d+(?:\.\d+)?", lambda m: _number_words(round(float(m.group())), language), text)
    parts = re.split(r"(?<=[.!?;:])\s+", text)
    return [p for p in parts if re.search(r"[A-Za-z]", p)]


def _to_wav(samples, rate: int) -> bytes:
    import numpy as np

    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(pcm.tobytes())
    return buffer.getvalue()


def _key(text: str, language: str) -> str:
    return hashlib.sha1(f"{language}:{text}".encode()).hexdigest()


def warm_up() -> None:
    """Load both voices in the background when the API starts."""
    if not settings.preload_voices:
        return  # small servers: voices load on first use instead
    # Even the import checks are slow, so all of it runs off the start-up path.
    _worker.submit(_warm)


def _warm() -> None:
    try:
        if _use_kasanoma("NY"):
            _piper()
        if _has_mms():
            for language in MODELS:
                if not _use_kasanoma(language):
                    _model(language)
    except Exception:  # noqa: BLE001 - voices load again on first use
        log.exception("Could not preload the voices")


def prepare(text: str, language: str) -> None:
    """Start making the audio now, so Listen plays at once later."""
    if available() and text:
        _submit(text, "NY" if language == "NY" else "EN")


def _submit(text: str, language: str) -> Future:
    key = _key(text, language)
    with _pending_lock:
        if key not in _pending:
            future = _worker.submit(_generate, text, language, key)
            future.add_done_callback(lambda _: _pending.pop(key, None))
            _pending[key] = future
        return _pending[key]


def synthesize(text: str, language: str) -> bytes:
    """WAV audio of `text` spoken in Chichewa (NY) or English (EN)."""
    language = "NY" if language == "NY" else "EN"
    key = _key(text, language)
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]
    return _submit(text, language).result()


def _generate(text: str, language: str, key: str) -> bytes:
    import numpy as np
    import torch

    if key in _cache:
        return _cache[key]

    if _use_kasanoma(language):
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as out:
            _piper().synthesize_wav(" ".join(_sentences(text, language)), out)
        return _remember(key, buffer.getvalue())

    model, tokenizer = _model(language)
    rate = model.config.sampling_rate
    pause = np.zeros(int(rate * 0.25), dtype="float32")
    pieces = []
    with torch.no_grad():
        for sentence in _sentences(text, language):
            inputs = tokenizer(sentence, return_tensors="pt")
            if inputs["input_ids"].shape[-1] == 0:
                continue
            pieces.append(model(**inputs).waveform[0].numpy())
            pieces.append(pause)
    return _remember(key, _to_wav(np.concatenate(pieces) if pieces else pause, rate))


def _remember(key: str, audio: bytes) -> bytes:
    _cache[key] = audio
    if len(_cache) > CACHE_SIZE:
        _cache.popitem(last=False)
    return audio
