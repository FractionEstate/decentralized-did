import json
from pathlib import Path

from decentralized_did.biometrics.aggregator import aggregate_finger_digests
from decentralized_did.biometrics.feature_extractor import (
    FingerTemplate,
    Minutia,
    minutiae_from_dicts,
)
from decentralized_did.biometrics.fuzzy_extractor import FuzzyExtractor
from decentralized_did.did.generator import build_did


FIXTURE_PATH = Path(__file__).parent.parent / "examples" / "sample_fingerprints.json"


def load_sample_templates():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    templates = []
    for entry in payload["fingers"]:
        templates.append(
            FingerTemplate(
                finger_id=entry["finger_id"],
                minutiae=minutiae_from_dicts(entry["minutiae"]),
            )
        )
    return payload["wallet_address"], templates


def jitter(template: FingerTemplate) -> FingerTemplate:
    jittered = []
    for idx, (qx, qy, qa) in enumerate(template.quantized):
        # Reverse the quantization for a close-but-not-identical scan
        x = (qx * template.grid_size) + (0.18 * template.grid_size if idx % 2 == 0 else -0.12 * template.grid_size)
        y = (qy * template.grid_size) + (0.14 * template.grid_size if idx % 2 == 1 else -0.16 * template.grid_size)
        angle_step = (qa / template.angle_bins) * 360.0
        angle = angle_step + (0.12 if idx % 2 == 0 else -0.10)
        jittered.append(Minutia(x=x, y=y, angle=angle))
    return FingerTemplate(template.finger_id, jittered, template.grid_size, template.angle_bins)


def test_quantization_stability():
    base = [Minutia(1.000, 1.000, 30.0), Minutia(1.250, 0.950, 60.0)]
    template_a = FingerTemplate("thumb", base)
    perturbed = [Minutia(1.004, 1.001, 29.7), Minutia(1.247, 0.948, 60.2)]
    template_b = FingerTemplate("thumb", perturbed)
    assert template_a.distance(template_b) == 0


def test_fuzzy_extractor_roundtrip():
    base = [Minutia(2.1, 3.4, 45.0), Minutia(2.6, 3.7, 120.0)]
    template = FingerTemplate("index", base)
    extractor = FuzzyExtractor()
    digest, helper = extractor.generate(template)
    reproduced = extractor.reproduce(template, helper)
    assert digest == reproduced


def test_end_to_end_verification():
    wallet_address, templates = load_sample_templates()
    extractor = FuzzyExtractor()

    enroll_digests = []
    helpers = []
    for template in templates:
        digest, helper = extractor.generate(template)
        enroll_digests.append((template.finger_id, digest))
        helpers.append(helper)

    master_digest = aggregate_finger_digests(enroll_digests)
    did = build_did(wallet_address, master_digest)
    assert did.startswith("did:cardano:")

    verify_digests = []
    for template, helper in zip(templates, helpers):
        noisy_template = jitter(template)
        digest = extractor.reproduce(noisy_template, helper)
        verify_digests.append((template.finger_id, digest))

    verify_master = aggregate_finger_digests(verify_digests)
    assert verify_master == master_digest
