from __future__ import annotations

import os
from vastai import Worker, WorkerConfig, HandlerConfig, BenchmarkConfig, LogActionConfig

MODEL_PORT = int(os.environ.get("MODEL_SERVER_PORT", "18000"))
MODEL_LOG = os.environ.get("MODEL_LOG_FILE", "/var/log/morphly/backend.log")

worker_config = WorkerConfig(
    model_server_url="http://127.0.0.1",
    model_server_port=MODEL_PORT,
    model_log_file=MODEL_LOG,
    model_healthcheck_url="/health",
    max_sessions=2,
    handlers=[
        HandlerConfig(
            route="/diagnostics",
            allow_parallel_requests=False,
            max_queue_time=30.0,
            workload_calculator=lambda payload: 1.0,
            benchmark_config=BenchmarkConfig(
                dataset=[{}],
                runs=1,
                concurrency=1,
            ),
        ),
    ],
    log_action_config=LogActionConfig(
        on_load=["INFO:     Application startup complete."],
        on_error=["Traceback (most recent call last):", "ERROR:"],
        on_info=["MORPHLY_"],
    ),
)

Worker(worker_config).run()
