class BlockReverb:
    def __init__(self, impulse, block_size=4, wet=0.5, dry=0.5):
        if len(impulse) == 0:
            raise ValueError("impulse must not be empty")
        if isinstance(block_size, bool) or not isinstance(block_size, int) or block_size <= 0:
            raise ValueError("block_size must be a positive integer")
        for name, value in (("wet", wet), ("dry", dry)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a number in [0, 1]")
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{name} must be in [0, 1]")

        self._impulse = list(impulse)
        self._block_size = block_size
        self._wet = float(wet)
        self._dry = float(dry)
        self.reset()

    def _linear_convolution(self, samples):
        conv = [0.0] * (len(samples) + len(self._impulse) - 1)
        for start in range(0, len(samples), self._block_size):
            block = samples[start:start + self._block_size]
            for i, sample in enumerate(block):
                for j, coeff in enumerate(self._impulse):
                    conv[start + i + j] += sample * coeff
        return conv

    def process(self, samples):
        if len(samples) == 0:
            return []
        conv = self._linear_convolution(samples)
        output = []
        for i, value in enumerate(conv):
            mixed = self._wet * value
            if i < len(samples):
                mixed += self._dry * samples[i]
            output.append(mixed)
        return output

    def _merge_part(self, chunk, output):
        carry = self._carry
        merged = [0.0] * (len(chunk) + len(self._impulse) - 1)
        for k, value in enumerate(carry):
            if value:
                merged[k] += value
        for i, sample in enumerate(chunk):
            for j, coeff in enumerate(self._impulse):
                merged[i + j] += sample * coeff
        for k, sample in enumerate(chunk):
            output.append(self._wet * merged[k] + self._dry * sample)
        self._carry = merged[len(chunk):]

    def push(self, block):
        self._processed += len(block)
        self._buffer.extend(block)
        output = []
        while len(self._buffer) >= self._block_size:
            chunk = self._buffer[:self._block_size]
            del self._buffer[:self._block_size]
            self._merge_part(chunk, output)
        if self._buffer:
            chunk = self._buffer
            self._buffer = []
            self._merge_part(chunk, output)
        return output

    def flush(self):
        tail = [self._wet * value for value in self._carry]
        self._carry = []
        self._buffer = []
        return tail

    def reset(self):
        self._buffer = []
        self._carry = []
        self._processed = 0

    def state(self):
        return {
            "impulse": list(self._impulse),
            "block_size": self._block_size,
            "wet": self._wet,
            "dry": self._dry,
            "input_samples": self._processed,
        }
