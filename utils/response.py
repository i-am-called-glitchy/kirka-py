class CommandResponse:
    def __init__(self):
        self.lines = []

    def add_section(self, content: str):
        self.lines.append(content)
        return self
    def add_error(self, message: str):
        self.lines.append(f"❌ Error: {message}")
        return self
    def overwrite_error(self, message:str):
        self.lines = [f"❌ Error: {message}"]
        return self
    def add_header(self, content:str):
        self.lines.append(f"*{content}* ")
    def build(self) -> str:
        return " -|- ".join(self.lines)