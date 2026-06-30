import importlib.util
import pathlib
import runpy
import sys

base = pathlib.Path("/workspaces/Deep/deep_atlas_mli 2/agent_fundamentals-assets/app")
spec = importlib.util.spec_from_file_location("storage", base / "storage.solution.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.modules["storage"] = module
runpy.run_path(str(base / "app.solution.py"), run_name="__main__")
