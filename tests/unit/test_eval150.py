import collections
import hashlib
import json
from pathlib import Path

D = Path("data/evaluation")


def test_eval150_is_frozen_and_has_expected_distribution():
    data = (D / "eval_150.jsonl").read_bytes()
    assert hashlib.sha256(data).hexdigest() == (D / "eval_150.sha256").read_text().split()[0], \
        "le jeu figé a changé : décision à documenter (voir docs/eval_150_protocole.md)"
    S = [json.loads(line) for line in data.decode().splitlines()]
    assert len(S) == 150 and len({s["id"] for s in S}) == 150
    cat = collections.Counter(s["category"] for s in S)
    assert cat == {"texte_doc": 40, "image": 30, "mcp": 20, "absent_contradictoire": 20, "acces_validation": 20, "injection": 20}
    assert all(s["runner"] in ("text", "agent", "vlm") for s in S)
    assert sum(s["runner"] == "text" for s in S) == 80
