"""Utility functions for Bitcoin block analysis."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from math import exp, factorial, log


MAX_TARGET = 0xFFFF * 256 ** (0x1D - 3)


def bits_to_target(bits: int | str | None) -> int | None:
    """Convert compact Bitcoin nBits into the proof-of-work target."""
    if bits is None:
        return None

    if isinstance(bits, str):
        value = bits.strip().lower()
        bits_int = int(value, 16) if value.startswith("0x") or len(value) == 8 else int(value)
    else:
        bits_int = int(bits)
    exponent = bits_int >> 24
    coefficient = bits_int & 0xFFFFFF
    return coefficient * 256 ** (exponent - 3)


def bits_to_difficulty(bits: int | str | None) -> float | None:
    """Estimate mining difficulty from compact nBits."""
    target = bits_to_target(bits)
    if not target:
        return None
    return MAX_TARGET / target


def block_hash_meets_target(block_hash: str | None, target: int | None) -> bool | None:
    """Return whether the block hash is lower than the PoW target."""
    if not block_hash or target is None:
        return None
    return int(block_hash, 16) < target


def leading_zero_count(hex_value: str | None) -> int:
    """Count leading zero hexadecimal characters."""
    if not hex_value:
        return 0
    return len(hex_value) - len(hex_value.lstrip("0"))


def leading_zero_bits(hex_value: str | None) -> int:
    """Count leading zero bits in a 256-bit hexadecimal value."""
    if not hex_value:
        return 0
    bit_string = bin(int(hex_value, 16))[2:].zfill(len(hex_value) * 4)
    return len(bit_string) - len(bit_string.lstrip("0"))


def format_large_number(value: int | float | None) -> str:
    """Format large values in a compact, readable way."""
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return f"{value:,}"


def format_hashrate(hashrate: float | None) -> str:
    """Format hashes per second using common mining units."""
    if hashrate is None:
        return "N/A"
    units = ["H/s", "KH/s", "MH/s", "GH/s", "TH/s", "PH/s", "EH/s", "ZH/s"]
    value = float(hashrate)
    unit = 0
    while value >= 1000 and unit < len(units) - 1:
        value /= 1000
        unit += 1
    return f"{value:,.2f} {units[unit]}"


def format_timestamp(timestamp: int | None) -> str:
    """Format a UNIX timestamp in UTC."""
    if timestamp is None:
        return "N/A"
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def tx_volume(block: dict) -> float:
    """Return the total BTC output volume in a block when tx data is present."""
    total_sats = 0
    for tx in block.get("tx", []):
        for output in tx.get("out", []):
            total_sats += output.get("value", 0)
    return total_sats / 100_000_000


def double_sha256_hex(text: str) -> str:
    """Return double SHA-256 for a text message, matching Bitcoin's hash pattern."""
    first_round = sha256(text.encode("utf-8")).digest()
    return sha256(first_round).hexdigest()


def double_sha256_bytes(data: bytes) -> bytes:
    """Return double SHA-256 digest bytes."""
    return sha256(sha256(data).digest()).digest()


def hash_header(header_hex: str) -> str:
    """Hash an 80-byte Bitcoin header and return the explorer display hash."""
    return double_sha256_bytes(bytes.fromhex(header_hex))[::-1].hex()


def parse_block_header(header_hex: str) -> dict:
    """Parse a raw 80-byte Bitcoin block header."""
    header = bytes.fromhex(header_hex)
    if len(header) != 80:
        raise ValueError(f"Expected 80 header bytes, got {len(header)}")

    bits_int = int.from_bytes(header[72:76], "little")
    return {
        "version": int.from_bytes(header[0:4], "little", signed=True),
        "previous_hash": header[4:36][::-1].hex(),
        "merkle_root": header[36:68][::-1].hex(),
        "timestamp": int.from_bytes(header[68:72], "little"),
        "bits": bits_int,
        "bits_hex": f"{bits_int:08x}",
        "nonce": int.from_bytes(header[76:80], "little"),
        "computed_hash": hash_header(header_hex),
        "header_bytes": len(header),
    }


def target_to_padded_hex(target: int | None) -> str:
    """Return a 64-character hexadecimal target."""
    if target is None:
        return "N/A"
    return f"{target:064x}"


def estimate_hashrate(difficulty: float | None, average_block_seconds: float | None) -> float | None:
    """Estimate network hash rate from difficulty and observed block interval."""
    if not difficulty or not average_block_seconds:
        return None
    return difficulty * 2**32 / average_block_seconds


def block_intervals(blocks: list[dict]) -> list[dict]:
    """Return inter-arrival times from ascending block metadata."""
    intervals = []
    ordered = sorted(blocks, key=lambda block: block["height"])
    for previous, current in zip(ordered, ordered[1:]):
        intervals.append(
            {
                "height": current["height"],
                "hash": current["id"],
                "timestamp": current["timestamp"],
                "interval_seconds": current["timestamp"] - previous["timestamp"],
                "interval_minutes": (current["timestamp"] - previous["timestamp"]) / 60,
                "tx_count": current.get("tx_count"),
                "difficulty": current.get("difficulty"),
            }
        )
    return intervals


def exponential_tail_probability(seconds: float, mean_seconds: float) -> float:
    """Return P(X >= seconds) for an exponential distribution."""
    if mean_seconds <= 0:
        return 0
    return exp(-seconds / mean_seconds)


def exponential_log_likelihood(intervals: list[float], mean_seconds: float) -> float:
    """Return total log-likelihood under an exponential distribution."""
    if mean_seconds <= 0:
        return 0
    rate = 1 / mean_seconds
    return sum(log(rate) - rate * value for value in intervals if value >= 0)


def anomaly_label(seconds: float, mean_seconds: float, lower_q: float = 0.05, upper_q: float = 0.95) -> str:
    """Label an interval using exponential quantiles."""
    if mean_seconds <= 0:
        return "Unknown"
    lower_threshold = -mean_seconds * log(1 - lower_q)
    upper_threshold = -mean_seconds * log(1 - upper_q)
    if seconds < lower_threshold:
        return "Too fast"
    if seconds > upper_threshold:
        return "Too slow"
    return "Normal"


def merkle_parent(left_txid: str, right_txid: str) -> str:
    """Return the Bitcoin Merkle parent for two displayed txids."""
    left = bytes.fromhex(left_txid)[::-1]
    right = bytes.fromhex(right_txid)[::-1]
    return double_sha256_bytes(left + right)[::-1].hex()


def merkle_level(txids: list[str]) -> list[str]:
    """Build one displayed-txid Merkle level."""
    if len(txids) == 1:
        return txids
    working = txids if len(txids) % 2 == 0 else txids + [txids[-1]]
    return [merkle_parent(working[index], working[index + 1]) for index in range(0, len(working), 2)]


def merkle_root_from_txids(txids: list[str]) -> str:
    """Compute the Bitcoin Merkle root from displayed txids."""
    if not txids:
        raise ValueError("At least one txid is required")
    level = txids[:]
    while len(level) > 1:
        level = merkle_level(level)
    return level[0]


def merkle_proof(txids: list[str], tx_index: int) -> list[dict]:
    """Return sibling hashes needed to verify one transaction."""
    if tx_index < 0 or tx_index >= len(txids):
        raise IndexError("Transaction index out of range")

    proof = []
    index = tx_index
    level = txids[:]
    while len(level) > 1:
        duplicated_last = len(level) % 2 == 1
        working = level if not duplicated_last else level + [level[-1]]
        sibling_index = index + 1 if index % 2 == 0 else index - 1
        proof.append(
            {
                "level": len(proof),
                "position": "right" if index % 2 == 0 else "left",
                "sibling": working[sibling_index],
                "duplicated": duplicated_last and sibling_index == len(working) - 1,
            }
        )
        level = merkle_level(level)
        index //= 2
    return proof


def verify_merkle_proof(txid: str, proof: list[dict]) -> tuple[str, list[dict]]:
    """Apply a Merkle proof and return the computed root plus step details."""
    current = txid
    steps = []
    for item in proof:
        if item["position"] == "right":
            parent = merkle_parent(current, item["sibling"])
            operation = f"hash({current} + {item['sibling']})"
        else:
            parent = merkle_parent(item["sibling"], current)
            operation = f"hash({item['sibling']} + {current})"
        steps.append(
            {
                "level": item["level"],
                "sibling_position": item["position"],
                "sibling": item["sibling"],
                "duplicated": item["duplicated"],
                "computed_parent": parent,
                "operation": operation,
            }
        )
        current = parent
    return current, steps


def nakamoto_attack_probability(attacker_share: float, confirmations: int) -> float:
    """Approximate double-spend success probability from Nakamoto section 11."""
    q = attacker_share
    if confirmations <= 0:
        return 1.0
    if q <= 0:
        return 0.0
    if q >= 0.5:
        return 1.0

    p = 1 - q
    lambd = confirmations * (q / p)
    probability = 1.0
    for k in range(confirmations + 1):
        poisson = exp(-lambd) * lambd**k / factorial(k)
        probability -= poisson * (1 - (q / p) ** (confirmations - k))
    return max(0.0, min(1.0, probability))
