#!/usr/bin/env python3
"""Bounded, machine-readable state management for the hourly reel mission."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def default_state(max_cycles: int) -> dict:
    return {
        "mission": "3000_HINDI_RESEARCH_REELS",
        "max_cycles": max_cycles,
        "cycles_completed": 0,
        "next_reel_id": "REEL_0003",
        "next_batch": "Batch_001",
        "last_status": "not_started",
        "history": [],
    }


def load(path: Path, max_cycles: int) -> dict:
    if not path.exists():
        return default_state(max_cycles)
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise SystemExit('BLOCKED: mission state must be a JSON object')
    data.setdefault('max_cycles', max_cycles)
    data.setdefault('cycles_completed', 0)
    data.setdefault('history', [])
    return data


def atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def start_cycle(path: Path, max_cycles: int) -> int:
    data = load(path, max_cycles)
    completed = int(data.get('cycles_completed', 0))
    if completed >= max_cycles:
        data['last_status'] = 'max_cycles_reached'
        data['updated_at_utc'] = utc_now()
        atomic_write(path, data)
        print(json.dumps({'should_run': False, 'reason': 'max_cycles_reached', 'cycles_completed': completed}))
        return 0

    cycle = completed + 1
    entry = {
        'cycle': cycle,
        'started_at_utc': utc_now(),
        'status': 'started',
        'reel_id': data.get('next_reel_id', 'REEL_0003'),
        'batch': data.get('next_batch', 'Batch_001'),
    }
    data['cycles_completed'] = cycle
    data['last_status'] = 'started'
    data['last_cycle'] = entry
    data['history'] = (data.get('history') or [])[-2399:] + [entry]
    data['updated_at_utc'] = entry['started_at_utc']
    atomic_write(path, data)
    print(json.dumps({'should_run': True, 'cycle': cycle, 'reel_id': entry['reel_id'], 'batch': entry['batch']}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['start'])
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--max-cycles', type=int, default=2400)
    args = parser.parse_args()
    if args.max_cycles < 1:
        raise SystemExit('BLOCKED: max-cycles must be positive')
    return start_cycle(args.state, args.max_cycles)


if __name__ == '__main__':
    raise SystemExit(main())
