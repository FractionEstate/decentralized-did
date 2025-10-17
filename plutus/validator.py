from dataclasses import dataclass
from opshin.prelude_v3 import *

# Redeemer for the biometric validator


@dataclass
class BiometricRedeemer(PlutusData):
    CONSTR_ID = 0
    message: bytes
    signature: bytes

# Datum for the biometric validator


@dataclass
class BiometricDatum(PlutusData):
    CONSTR_ID = 0
    pub_key: bytes


def validator(datum: BiometricDatum, redeemer: BiometricRedeemer, context: ScriptContext) -> None:
    """
    A simple Plutus V3 validator that verifies a signature.
    """
    assert verify_ed25519_signature(
        datum.pub_key, redeemer.message, redeemer.signature), "Signature verification failed"
