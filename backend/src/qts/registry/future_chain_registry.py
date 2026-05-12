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
        """Perform __post_init__."""
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
        """Perform __post_init__."""
        if not self.root_symbol.strip():
            raise ValueError("root_symbol must not be empty")
        if self.offset < 0:
            raise ValueError("offset must be non-negative")


class FutureChainRegistry:
    """Resolve future roots to concrete tradable contracts."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._chains: dict[str, FutureChain] = {}

    def register(self, chain: FutureChain) -> None:
        """Perform register."""
        self._chains[self._normalize_root(chain.root_symbol)] = chain

    def resolve_contract(self, root_symbol: str, *, offset: int = 0) -> InstrumentId:
        """Perform resolve_contract."""
        chain = self._get_chain(root_symbol)
        try:
            return chain.contracts[offset]
        except IndexError as exc:
            raise KeyError(
                f"future contract offset not available: {root_symbol}[{offset}]"
            ) from exc

    def require_tradable(self, reference: InstrumentId | ContinuousFutureRef) -> InstrumentId:
        """Perform require_tradable."""
        if isinstance(reference, ContinuousFutureRef):
            raise ValueError("continuous future references are not directly tradable")
        return reference

    def _get_chain(self, root_symbol: str) -> FutureChain:
        """Perform _get_chain."""
        root = self._normalize_root(root_symbol)
        try:
            return self._chains[root]
        except KeyError as exc:
            raise KeyError(f"missing future chain: {root_symbol}") from exc

    @staticmethod
    def _normalize_root(root_symbol: str) -> str:
        """Perform _normalize_root."""
        normalized = root_symbol.strip().upper()
        if not normalized:
            raise ValueError("root_symbol must not be empty")
        return normalized


__all__ = ["ContinuousFutureRef", "FutureChain", "FutureChainRegistry"]
