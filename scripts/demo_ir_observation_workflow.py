"""Historical synthetic observation registry; no sends or real-company outcomes."""
from copy import deepcopy
import argparse
from hashlib import sha256
import json
from pathlib import Path

from ir_agent.models import json_text, load_json
from ir_agent.observation_store import ObservationStore
from ir_agent.observations import summarize_observations
from ir_agent.store import Store

ROOT = Path(__file__).resolve().parents[1]


def run_demo(include_correction=False):
    complete = load_json(ROOT / 'examples/ir-observations.json')['records'][0]
    complete['verification']['recorded_at'] = '2026-10-10T16:00:00+09:00'
    evidence = complete['verification']['evidence'][0]
    evidence.update(published_at='2026-10-10T15:00:00+09:00', retrieved_at='2026-10-10T15:30:00+09:00')
    design = deepcopy(complete)
    for key in ('dispatch', 'response_check', 'verification'):
        design.pop(key)
    design['replies'] = []
    db = Store(':memory:')
    try:
        registry = ObservationStore(db.connection)
        registry.register(design, '2026-10-01T10:01:00+09:00')
        design['dispatch'] = complete['dispatch']
        registry.append(design, 1, '2026-10-01T10:02:00+09:00')
        design['replies'] = complete['replies']
        registry.append(design, 2, '2026-10-02T10:01:00+09:00')
        design['verification'] = complete['verification']
        registry.append(design, 3, '2026-10-10T16:00:00+09:00')
        before = '2026-10-09T16:00:00+09:00'
        after = '2026-10-10T16:00:00+09:00'
        earlier = summarize_observations(registry.records_as_of(before), as_of=before)
        later = summarize_observations(registry.records_as_of(after), as_of=after)
        result = {'synthetic': True, 'description': 'Explicitly injected historical paper timestamps and invented observations',
                'external_sends': 0, 'network_requests': 0,
                'observation_versions': len(registry.history(design['id'])),
                'eligible_before_verification': earlier['eligible_count'],
                'eligible_after_verification': later['eligible_count'],
                'calibration_status': later['calibration_status'], 'later_summary': later}
        if include_correction:
            reply = deepcopy(design['replies'][0])
            corrected_at = '2026-10-11T16:00:00+09:00'
            design['assessments'] = [{
                'id': 'synthetic-public-basis-recheck', 'target_kind': 'reply', 'target_id': reply['id'],
                'target_snapshot_sha256': sha256(json_text(reply).encode()).hexdigest(),
                'version': 1, 'expected_previous_version': 0, 'recorded_at': corrected_at,
                'reviewer': 'Synthetic demo worker',
                'rationale': 'Recheck the public basis; this fixture has no independently bound raw reply.',
                'basis': {'public_evidence_references': []},
                'assessment': {'signal': reply['signal'], 'information_status': 'unclear'}}]
            saved = registry.append(design, 4, corrected_at)
            corrected = summarize_observations(registry.records_as_of(corrected_at), as_of=corrected_at)
            historical = summarize_observations(registry.records_as_of(after), as_of=after)
            result.update(observation_versions=len(registry.history(design['id'])),
                          correction={'binding_status': saved['record']['assessments'][0]['basis_verification']['status'],
                                      'eligible_before_correction': historical['eligible_count'],
                                      'eligible_after_correction': corrected['eligible_count'],
                                      'original_reply_unchanged': saved['record']['replies'][0] == reply,
                                      'summary': corrected})
        return result
    finally:
        db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-correction', action='store_true', help='Also append an unverified safety hold without altering the original reply')
    args = parser.parse_args()
    print(json.dumps(run_demo(args.with_correction), ensure_ascii=False, indent=2, allow_nan=False))
