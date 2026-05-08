"""Public Bitcoin API client used by the dashboard modules."""

import requests

BLOCKCHAIN_BASE_URL = "https://blockchain.info"
BLOCKSTREAM_BASE_URL = "https://blockstream.info/api"


def _get_json(url: str, **kwargs) -> dict | list:
    response = requests.get(url, timeout=15, **kwargs)
    response.raise_for_status()
    return response.json()


def _get_text(url: str) -> str:
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.text.strip()


def get_latest_block() -> dict:
    """Return the latest block summary."""
    return _get_json(f"{BLOCKCHAIN_BASE_URL}/latestblock")


def get_block(block_hash: str) -> dict:
    """Return full details for a block identified by *block_hash*."""
    block_hash = block_hash.strip()
    return _get_json(f"{BLOCKCHAIN_BASE_URL}/rawblock/{block_hash}")


def get_latest_full_block() -> dict:
    """Return full details for the current latest Bitcoin block."""
    latest = get_latest_block()
    return get_block(latest["hash"])


def get_tip_height() -> int:
    """Return the current Bitcoin tip height from Blockstream."""
    return int(_get_text(f"{BLOCKSTREAM_BASE_URL}/blocks/tip/height"))


def get_block_hash_by_height(height: int) -> str:
    """Return the block hash at a given height."""
    return _get_text(f"{BLOCKSTREAM_BASE_URL}/block-height/{height}")


def get_blockstream_block(block_hash: str) -> dict:
    """Return Blockstream block metadata for *block_hash*."""
    return _get_json(f"{BLOCKSTREAM_BASE_URL}/block/{block_hash.strip()}")


def get_block_header(block_hash: str) -> str:
    """Return the raw 80-byte block header as hexadecimal text."""
    return _get_text(f"{BLOCKSTREAM_BASE_URL}/block/{block_hash.strip()}/header")


def get_block_txids(block_hash: str) -> list[str]:
    """Return all transaction ids for a block."""
    return _get_json(f"{BLOCKSTREAM_BASE_URL}/block/{block_hash.strip()}/txids")


def get_latest_blockstream_block() -> dict:
    """Return the latest block metadata from Blockstream."""
    height = get_tip_height()
    return get_blockstream_block(get_block_hash_by_height(height))


def get_blockstream_blocks_page(start_height: int | None = None) -> list[dict]:
    """Return one Blockstream page with up to 10 blocks descending from start height."""
    if start_height is None:
        return _get_json(f"{BLOCKSTREAM_BASE_URL}/blocks")
    return _get_json(f"{BLOCKSTREAM_BASE_URL}/blocks/{start_height}")


def get_recent_blocks(count: int = 30) -> list[dict]:
    """Return recent blocks sorted by ascending height."""
    blocks: list[dict] = []
    next_height: int | None = None

    while len(blocks) < count:
        page = get_blockstream_blocks_page(next_height)
        if not page:
            break
        blocks.extend(page)
        next_height = min(block["height"] for block in page) - 1

    return sorted(blocks[:count], key=lambda block: block["height"])


def get_blocks_by_heights(heights: list[int]) -> list[dict]:
    """Return block metadata for the provided heights."""
    blocks = []
    for height in heights:
        block_hash = get_block_hash_by_height(height)
        blocks.append(get_blockstream_block(block_hash))
    return blocks


def get_difficulty_history(n_points: int = 100) -> list[dict]:
    """Return the last *n_points* difficulty values as a list of dicts."""
    response = requests.get(
        f"{BLOCKCHAIN_BASE_URL}/charts/difficulty",
        params={"timespan": "1year", "format": "json", "sampled": "true"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("values", [])[-n_points:]
