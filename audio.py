import array
import math

try:
    import sounddevice as sd
except Exception:
    sd = None


class ShoutMeter:
    def __init__(self, threshold):
        self.threshold = threshold
        self.volume = 0.0
        self.available = False
        self.error = None
        self.stream = None
        self.was_loud = False

    def start(self):
        if sd is None:
            self.error = "Mic unavailable - hold Space to charge."
            return

        try:
            self.stream = sd.RawInputStream(
                samplerate=16000,
                blocksize=1024,
                channels=1,
                dtype="int16",
                callback=self._audio_callback,
            )
            self.stream.start()
            self.available = True
        except Exception:
            self.error = "Mic unavailable - hold Space to charge."
            self.available = False

    def stop(self):
        if self.stream is None:
            return

        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass
        self.stream = None

    def _audio_callback(self, indata, frames, time_info, status):
        samples = array.array("h")
        samples.frombytes(bytes(indata))
        if not samples:
            self.volume = 0.0
            return

        square_sum = sum(sample * sample for sample in samples)
        rms = math.sqrt(square_sum / len(samples)) / 32768
        self.volume = min(1.0, rms)

    def consume_shout(self):
        is_loud = self.available and self.volume >= self.threshold
        if is_loud and not self.was_loud:
            self.was_loud = True
            return True

        if not is_loud:
            self.was_loud = False

        return False

    def power_ratio(self):
        return min(1.0, self.volume / self.threshold)
