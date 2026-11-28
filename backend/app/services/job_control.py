"""
统一作业暂停/续跑控制

四个长流程（图谱构建、环境准备、模拟运行、报告生成）都需要支持：
- 暂停：在当前可控边界停下，保留已完成的工作
- 续跑：从停下的位置继续，而不是从头重来
- 停止：彻底终止（模拟阶段等价于结束进程）

设计要点：
- 暂停是"协作式"的：工作线程/子进程在安全的检查点轮询暂停标志。
- 状态持久化到磁盘，进程重启或页面重开后可恢复控制关系。
- 所有外部依赖（Zep batch、OASIS 数据库）都是幂等或可复用的，因此
  "续跑"本身优先复用已有产物，失败时才回退为从头开始。
"""

import os
import json
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger('omniprediction.job_control')


class JobPhase(str, Enum):
    """作业（流程阶段）标识"""
    GRAPH_BUILD = "graph_build"
    SIMULATION_PREPARE = "prepare"
    SIMULATION_RUN = "simulation"
    REPORT = "report"


class JobState(str, Enum):
    """作业状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


class JobPauseSignal:
    """
    单个作业的暂停信号。

    工作线程在检查点调用 checkpoint()：
    - 若要求暂停，则阻塞直到 resume() 或 cancel()。
    - 若要求停止，则抛出 JobCancelled，由上层清理并落到 STOPPED。
    """

    def __init__(self, job_key: str):
        self.job_key = job_key
        self._lock = threading.Lock()
        self._resume_event = threading.Event()
        self._resume_event.set()  # 默认不暂停
        self._cancelled = False

    def pause(self) -> None:
        with self._lock:
            self._resume_event.clear()

    def resume(self) -> None:
        with self._lock:
            self._cancelled = False
            self._resume_event.set()

    def cancel(self) -> None:
        with self._lock:
            self._cancelled = True
            self._resume_event.set()

    @property
    def is_paused(self) -> bool:
        return not self._resume_event.is_set()

    @property
    def is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def checkpoint(self, poll_seconds: float = 0.5) -> None:
        """在安全边界调用。阻塞处理暂停；取消则抛异常。"""
        if self.is_cancelled:
            raise JobCancelled(self.job_key)
        if self._resume_event.is_set():
            return
        logger.info(f"作业 {self.job_key} 已暂停，等待继续...")
        while not self._resume_event.wait(timeout=poll_seconds):
            pass
        if self.is_cancelled:
            raise JobCancelled(self.job_key)
        logger.info(f"作业 {self.job_key} 已继续")


class JobCancelled(Exception):
    """作业被取消时在检查点抛出"""

    def __init__(self, job_key: str):
        self.job_key = job_key
        super().__init__(f"作业已取消: {job_key}")


class JobControl:
    """进程内作业控制注册表（线程安全单例）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._signals: Dict[str, JobPauseSignal] = {}
                    cls._instance._guard = threading.Lock()
        return cls._instance

    @staticmethod
    def make_key(phase: JobPhase, resource_id: str) -> str:
        return f"{phase.value}:{resource_id}"

    def get_or_create(self, key: str) -> JobPauseSignal:
        with self._guard:
            signal = self._signals.get(key)
            if signal is None:
                signal = JobPauseSignal(key)
                self._signals[key] = signal
            return signal

    def get(self, key: str) -> Optional[JobPauseSignal]:
        with self._guard:
            return self._signals.get(key)

    def drop(self, key: str) -> None:
        with self._guard:
            self._signals.pop(key, None)


class JobStateStore:
    """
    把作业状态持久化到磁盘，供前端轮询和页面重开后恢复。

    路径：uploads/jobs/{phase}/{resource_id}.json
    """

    ROOT_DIR = os.path.join(os.path.dirname(__file__), '../../uploads/jobs')

    @classmethod
    def _dir_for(cls, phase: JobPhase) -> str:
        path = os.path.join(cls.ROOT_DIR, phase.value)
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def _path_for(cls, phase: JobPhase, resource_id: str) -> str:
        safe_id = "".join(
            c for c in resource_id if c.isalnum() or c in "_-"
        ) or "unknown"
        return os.path.join(cls._dir_for(phase), f"{safe_id}.json")

    @classmethod
    def save(
        cls,
        phase: JobPhase,
        resource_id: str,
        state: JobState,
        *,
        progress: int = 0,
        message: str = "",
        resumable: bool = True,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "phase": phase.value,
            "resource_id": resource_id,
            "state": state.value,
            "progress": progress,
            "message": message,
            "resumable": resumable,
            "extra": extra or {},
            "updated_at": datetime.now().isoformat(),
        }
        path = cls._path_for(phase, resource_id)
        tmp = f"{path}.tmp"
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception as e:
            logger.warning(f"保存作业状态失败: {phase.value}/{resource_id}: {e}")
        return payload

    @classmethod
    def load(cls, phase: JobPhase, resource_id: str) -> Optional[Dict[str, Any]]:
        path = cls._path_for(phase, resource_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"读取作业状态失败: {phase.value}/{resource_id}: {e}")
            return None

    @classmethod
    def clear(cls, phase: JobPhase, resource_id: str) -> None:
        path = cls._path_for(phase, resource_id)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.warning(f"清理作业状态失败: {phase.value}/{resource_id}: {e}")


class PausableMonitor:
    """
    监控线程的暂停标志（跨进程共享，基于文件）。

    用于模拟子进程：Flask 侧写 PAUSE 文件，子进程在每轮开始时检查。
    文件内容随检查消费而删除，避免状态泄漏。
    """

    PAUSE_FILE = "pause.flag"

    def __init__(self, simulation_dir: str):
        self.simulation_dir = simulation_dir
        self.path = os.path.join(simulation_dir, self.PAUSE_FILE)

    def request_pause(self) -> None:
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(datetime.now().isoformat())

    def request_resume(self) -> None:
        try:
            if os.path.exists(self.path):
                os.remove(self.path)
        except OSError:
            pass

    def is_pause_requested(self) -> bool:
        return os.path.exists(self.path)


def wait_while_paused(simulation_dir: str, job_key: str = "") -> None:
    """
    供模拟子进程在轮次边界调用。

    暂停期间不消耗 LLM 调用；收到 resume（文件删除）后继续。
    """
    pause = PausableMonitor(simulation_dir)
    if not pause.is_pause_requested():
        return
    logger.info(f"模拟已暂停，等待继续: {job_key or simulation_dir}")
    while pause.is_pause_requested():
        time.sleep(1.0)
    logger.info(f"模拟已继续: {job_key or simulation_dir}")
