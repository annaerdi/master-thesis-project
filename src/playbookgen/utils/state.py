import yaml

class PlaybookState:
    def __init__(self):
        self.commands = []

    def add_step(self, step):
        self.commands.append(step)

    def to_yaml(self):
        return yaml.dump({"commands": self.commands}, sort_keys=False)
