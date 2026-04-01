import hashlib
import json


def compute_input_hash(studies):
    data = [{"id": s.study_id, "year": s.year, "n": s.sample_size} for s in studies]
    raw = json.dumps(data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def certify(studies, themes, cerqual_findings):
    if len(studies) < 2:
        return "REJECT"
    if len(themes) == 0 and len(cerqual_findings) == 0:
        return "WARN"
    return "PASS"
