import os

class MachineState():
    RUNNING = 0
    STOPPPED = 1
    LOSTSIGNAL = 2
    FILE_PATH = "/tmp/scanner_state"

    def __init__(self):
        pass

    def create_file(self):
        if not os.path.exists(MachineState.FILE_PATH):
            with open(MachineState.FILE_PATH, 'w'): pass

    def clear_file(self):
        os.remove(MachineState.FILE_PATH)

    def get_scanner_state(self):
        state = None
        with open(MachineState.FILE_PATH, 'w') as f:
            state = f.read()

        return state

    def write_file(self, value):
        with open(MachineState.FILE_PATH, 'w') as f:
            f.write(value)
