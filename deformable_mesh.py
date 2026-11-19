class MassSpringMesh:
    def __init__(self, positions, springs, masses=None, velocities=None,
                 stiffness=1.0, damping=0.0, pinned=()):
        pass

    def step(self, dt, gravity=(0.0, 0.0)):
        return None

    def positions(self):
        return []

    def velocities(self):
        return []

    def state(self):
        return {}
