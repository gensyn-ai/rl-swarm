from rgym_exp.vendor.genrl.communication.communication import Communication
from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger


class TestGameManager:
    def __init__(self, msg: str, comm: Communication | None = None):
        self.msg = msg
        self.comm = comm

    def run_game(self):
        if self.comm is not None:
            gathered_obj = self.comm.all_gather_object([1])
            get_logger().info(f"Run backend gather with output: {gathered_obj}")
        get_logger().info(f"Run game with message: {self.msg}")
