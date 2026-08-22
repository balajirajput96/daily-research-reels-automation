from __future__ import annotations

from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / '.github' / 'workflows' / 'hourly-reel-continuation.yml'


def test_hourly_workflow_contract() -> None:
    text = WORKFLOW.read_text(encoding='utf-8')
    assert "cron: '0 * * * *'" in text
    assert 'max-cycles 2400' in text
    assert 'GOOGLE_DRIVE_REFRESH_TOKEN' in text
    assert "git push origin HEAD:main" in text
    assert "steps.cycle.outputs.should_run == 'true'" in text
    assert 'Record blocked configuration' in text
    assert 'Run continuation adapter when Drive is configured' in text
