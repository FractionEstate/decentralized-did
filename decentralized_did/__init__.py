"""
Compatibility shim package.

When the repository root contains `sdk/src/decentralized_did` we want
`python -m decentralized_did.cli` (used by integration tests) to import
the SDK package. Tests and subprocesses sometimes run from a different
working directory or virtualenv where the editable install isn't present,
so we extend the package search path to include the SDK source tree when
available.

This file is intentionally small and only mutates __path__ so the real
package under `sdk/src/decentralized_did` is discoverable as submodules
like `decentralized_did.cli`.
"""
import os

_HERE = os.path.abspath(os.path.dirname(__file__))
_SDK_PKG = os.path.abspath(os.path.join(
    _HERE, os.pardir, "sdk", "src", "decentralized_did"))

if os.path.isdir(_SDK_PKG) and _SDK_PKG not in __path__:
    # Prepend so local SDK code takes precedence when importing submodules
    # from this top-level package. This keeps tests and `python -m` usage
    # working without requiring an editable install.
    __path__.insert(0, _SDK_PKG)
