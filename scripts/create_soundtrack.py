"""Create Safar's original acoustic-style theme with a plucked-string model."""

from functools import lru_cache
from pathlib import Path
import wave

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 22_050
DURATION = 24.0
TOTAL = round(SAMPLE_RATE * DURATION)
LEFT = np.zeros(TOTAL, dtype=np.float64)
RIGHT = np.zeros(TOTAL, dtype=np.float64)


def frequency(note):
    return 440.0 * 2 ** ((note - 69) / 12)


@lru_cache(maxsize=128)
def plucked_string(note, frame_count, seed):
    """Karplus–Strong string model: a short noise burst fed back through a delay line."""
    delay = max(2, round(SAMPLE_RATE / frequency(note)))
    random = np.random.default_rng(seed)
    ring = random.uniform(-1.0, 1.0, delay)
    ring -= ring.mean()
    output = np.empty(frame_count, dtype=np.float64)
    cursor = 0
    for frame in range(frame_count):
        output[frame] = ring[cursor]
        next_cursor = (cursor + 1) % delay
        ring[cursor] = 0.498 * (ring[cursor] + ring[next_cursor])
        cursor = next_cursor
    times = np.arange(frame_count) / SAMPLE_RATE
    output *= np.exp(-2.0 * times)
    return output


def add_string(note, start, length, volume, pan=0.0, seed=0):
    first = max(0, round(start * SAMPLE_RATE))
    last = min(TOTAL, first + round(length * SAMPLE_RATE))
    if last <= first:
        return
    sample = plucked_string(note, last - first, seed)
    fade = min(1.0, max(1, sample.size) / (SAMPLE_RATE * 0.025))
    attack = np.minimum(1.0, np.arange(sample.size) / max(1, SAMPLE_RATE * 0.025))
    signal = sample * attack * volume * fade
    LEFT[first:last] += signal * np.sqrt((1 - pan) / 2)
    RIGHT[first:last] += signal * np.sqrt((1 + pan) / 2)


# A relaxed major-key progression with an original, singable pentatonic motif.
chords = (
    (48, 55, 60, 64, 67),  # C
    (43, 50, 55, 59, 62),  # G
    (41, 48, 53, 57, 60),  # F
    (48, 55, 60, 64, 67),  # C
)
melody = (76, 79, 81, 79, 76, 74, 72, 74, 76, 79, 84, 81, 79, 76, 74, 72)
bar_seconds = 3.0
beat_seconds = bar_seconds / 4
event = 0

for bar in range(round(DURATION / bar_seconds)):
    chord = chords[bar % len(chords)]
    start = bar * bar_seconds

    # A warm, quiet chord bed with a low root note underneath.
    for voice, note in enumerate(chord[:4]):
        add_string(note, start, 2.9, 0.052 if voice == 0 else 0.035, pan=-0.22 + voice * 0.14, seed=note * 19 + bar)
    add_string(chord[0] - 12, start, 1.8, 0.055, pan=-0.08, seed=chord[0] + bar)

    # Gentle alternating arpeggios provide movement without a heavy beat.
    pattern = (chord[2], chord[3], chord[4], chord[3])
    for beat, note in enumerate(pattern):
        note_time = start + beat * beat_seconds
        add_string(note + 12, note_time + 0.08, 0.82, 0.11, pan=0.2 if beat % 2 else -0.2, seed=100 + bar * 8 + beat)
        if beat in (0, 2):
            melody_index = (bar * 2 + beat // 2) % len(melody)
            add_string(melody[melody_index], note_time + 0.24, 0.98, 0.095, pan=0.12, seed=500 + bar * 2 + beat)
        event += 1

fade_in = np.minimum(1.0, np.arange(TOTAL) / (SAMPLE_RATE * 0.65))
fade_out = np.minimum(1.0, np.maximum(0.0, (TOTAL - np.arange(TOTAL)) / (SAMPLE_RATE * 0.9)))
stereo = np.column_stack((LEFT * fade_in * fade_out, RIGHT * fade_in * fade_out))
peak = np.max(np.abs(stereo))
if peak:
    stereo *= 0.28 / peak
pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")

destination = ROOT / "assets" / "safar_ambient.wav"
destination.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(destination), "wb") as soundtrack:
    soundtrack.setnchannels(2)
    soundtrack.setsampwidth(2)
    soundtrack.setframerate(SAMPLE_RATE)
    soundtrack.writeframes(pcm.tobytes())
print(f"Created {destination} ({destination.stat().st_size:,} bytes)")
