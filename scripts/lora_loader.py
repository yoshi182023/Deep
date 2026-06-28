import os
from pathlib import Path


class LazyLoraLoader:
    """Lazy loader for the local lora directory.

    This keeps the large checkpoint files on disk but avoids loading them
    until the user explicitly requests access.
    """

    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or os.path.join(os.getcwd(), "lora"))

    def exists(self) -> bool:
        return self.base_dir.exists()

    def list_checkpoints(self) -> list[str]:
        if not self.exists():
            return []
        return sorted([p.name for p in self.base_dir.iterdir() if p.is_dir()])

    def get_checkpoint(self, name: str):
        """Return the path to a checkpoint directory when requested."""
        checkpoint_path = self.base_dir / name
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint '{name}' not found under {self.base_dir}")
        return checkpoint_path

    def load_adapter(self, checkpoint_name: str):
        """Placeholder for actual adapter loading logic."""
        checkpoint_path = self.get_checkpoint(checkpoint_name)
        print(f"Loaded adapter from: {checkpoint_path}")
        return checkpoint_path
