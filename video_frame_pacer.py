class FramePacer:
    def __init__(self, fps=60):
        self.fps = fps

    def submit(self, pts):
        return None

    def present(self, now):
        return {}

    def stats(self):
        return {}

    def reset(self):
        return None

    def state(self):
        return {}
