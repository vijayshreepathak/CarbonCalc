from __future__ import annotations

import logging

import pathway as pw

from worker.config import load_config
from worker.pipeline import build_pipeline


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config()
    logging.info(
        "Starting Pathway worker: streams_dir=%s static_dir=%s outputs_dir=%s",
        cfg.streams_dir,
        cfg.static_dir,
        cfg.outputs_dir,
    )
    build_pipeline(cfg)
    pw.run()


if __name__ == "__main__":
    main()

