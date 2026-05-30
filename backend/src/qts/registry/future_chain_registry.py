"""Future chain registry and continuous future references."""

from __future__ import annotations

from dataclasses import dataclass

from qts.core.ids import InstrumentId


@dataclass(frozen=True, slots=True)
class FutureChain:
    """Ordered concrete future contracts for a root symbol."""

    root_symbol: str
    contracts: tuple[InstrumentId, ...]

    def __post_init__(self) -> None:
        """Validate the root symbol is non-empty and the chain is non-empty."""
        if not self.root_symbol.strip():
            raise ValueError("root_symbol must not be empty")
        if not self.contracts:
            raise ValueError("future chain must contain at least one contract")


@dataclass(frozen=True, slots=True)
class ContinuousFutureRef:
    """Research/data reference to a rolling future contract."""

    root_symbol: str
    offset: int = 0

    def __post_init__(self) -> None:
        """Validate the root symbol is non-empty and the offset is non-negative."""
        if not self.root_symbol.strip():
            raise ValueError("root_symbol must not be empty")
        if self.offset < 0:
            raise ValueError("offset must be non-negative")


class FutureChainRegistry:
    """Resolve future roots to concrete tradable contracts."""

    def __init__(self) -> None:
        """Initialize an empty registry of future chains keyed by root."""
        self._chains: dict[str, FutureChain] = {}

    def register(self, chain: FutureChain) -> None:
        """Store a future chain under its normalized root symbol."""
        self._chains[self._normalize_root(chain.root_symbol)] = chain

    def resolve_contract(self, root_symbol: str, *, offset: int = 0) -> InstrumentId:
        """Return the concrete contract at ``offset`` in the root's chain."""
        chain = self._get_chain(root_symbol)
        try:
            return chain.contracts[offset]
        except IndexError as exc:
            raise KeyError(
                f"future contract offset not available: {root_symbol}[{offset}]"
            ) from exc

    def require_tradable(self, reference: InstrumentId | ContinuousFutureRef) -> InstrumentId:
        """Return the instrument id, rejecting non-tradable continuous refs."""
        if isinstance(reference, ContinuousFutureRef):
            raise ValueError("continuous future references are not directly tradable")
        return reference

    def _get_chain(self, root_symbol: str) -> FutureChain:
        """Look up the registered chain for a root, raising when missing."""
        root = self._normalize_root(root_symbol)
        try:
            return self._chains[root]
        except KeyError as exc:
            raise KeyError(f"missing future chain: {root_symbol}") from exc

    @staticmethod
    def _normalize_root(root_symbol: str) -> str:
        """Return the trimmed, upper-cased root symbol used as the chain key."""
        normalized = root_symbol.strip().upper()
        if not normalized:
            raise ValueError("root_symbol must not be empty")
        return normalized


__all__ = ["ContinuousFutureRef", "FutureChain", "FutureChainRegistry"]
