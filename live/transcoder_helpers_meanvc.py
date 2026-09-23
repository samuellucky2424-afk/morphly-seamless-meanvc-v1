from __future__ import annotations

import logging
import os
import time

import numpy as np
import requests

logger = logging.getLogger("socketio_server_pubsub")

MEANVC_ENABLED = os.environ.get("MORPHLY_MEANVC_ENABLED", "1") == "1"
MEANVC_URL = os.environ.get("MORPHLY_MEANVC_URL", "http://127.0.0.1:8766")
_http = requests.Session()


def _run_meanvc(samples: list[float], sample_rate: int) -> tuple[list[float], int]:
    if not samples:
        return [], 16000

    x = np.asarray(samples, dtype="<f4")
    started = time.perf_counter()
    r = _http.post(
        f"{MEANVC_URL}/convert",
        data=x.tobytes(),
        headers={"X-Sample-Rate": str(int(sample_rate))},
        timeout=30,
    )
    r.raise_for_status()

    if not r.content:
        return [], 16000

    y = np.frombuffer(r.content, dtype="<f4")
    total_ms = (time.perf_counter() - started) * 1000.0
    meanvc_ms = r.headers.get("X-MeanVC-Proc-Ms", "?")
    logger.info(
        "MORPHLY_MEANVC in=%d@%s out=%d@16000 meanvc_ms=%s bridge_ms=%.1f",
        x.size,
        sample_rate,
        y.size,
        meanvc_ms,
        total_ms,
    )
    return y.astype(np.float32, copy=False).tolist(), 16000


def get_transcoder_output_events(transcoder) -> list:
    speech_and_text_output = transcoder.get_buffered_output()
    if speech_and_text_output is None:
        return []

    events = []

    if speech_and_text_output.speech_samples:
        payload = speech_and_text_output.speech_samples
        sample_rate = int(speech_and_text_output.speech_sample_rate)

        if MEANVC_ENABLED:
            try:
                payload, sample_rate = _run_meanvc(payload, sample_rate)
            except Exception:
                logger.exception("MeanVC bridge failed; falling back to raw Seamless speech")

        if payload:
            events.append(
                {
                    "event": "translation_speech",
                    "payload": payload,
                    "sample_rate": sample_rate,
                }
            )

    if speech_and_text_output.text:
        events.append(
            {
                "event": "translation_text",
                "payload": speech_and_text_output.text,
            }
        )

    for e in events:
        e["eos"] = speech_and_text_output.final

    return events
