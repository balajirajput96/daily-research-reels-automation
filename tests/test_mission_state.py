from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / 'scripts' / 'mission_state.py'


def run_state(path: Path, max_cycles: int = 3) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), 'start', '--state', str(path), '--max-cycles', str(max_cycles)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_first_cycle_is_reserved_and_persisted(tmp_path: Path) -> None:
    state = tmp_path / 'state.json'
    result = run_state(state)
    assert result == {'should_run': True, 'cycle': 1, 'reel_id': 'REEL_0003', 'batch': 'Batch_001'}
    saved = json.loads(state.read_text(encoding='utf-8'))
    assert saved['cycles_completed'] == 1
    assert saved['last_cycle']['status'] == 'started'


def test_state_resumes_and_stops_at_cap(tmp_path: Path) -> None:
    state = tmp_path / 'state.json'
    assert run_state(state) == {'should_run': True, 'cycle': 1, 'reel_id': 'REEL_0003', 'batch': 'Batch_001'}
    assert run_state(state) == {'should_run': True, 'cycle': 2, 'reel_id': 'REEL_0003', 'batch': 'Batch_001'}
    assert run_state(state) == {'should_run': True, 'cycle': 3, 'reel_id': 'REEL_0003', 'batch': 'Batch_001'}
    assert run_state(state) == {'should_run': False, 'reason': 'max_cycles_reached', 'cycles_completed': 3}
