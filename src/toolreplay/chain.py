"""SHA-256 chaining and verification.

Each record is sealed into a chain link. The digest of link N is computed over
the previous digest plus the canonical bytes of record N. Changing any earlier
record changes every later digest, so tampering anywhere is detectable by
recomputing the chain and comparing.

The genesis previous-digest is 64 zero hex characters.
"""

import hashlib
import json
from dataclasses import dataclass
