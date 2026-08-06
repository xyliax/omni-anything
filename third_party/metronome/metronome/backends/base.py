"""Backend interface — what Metronome needs from a serving engine.

Metronome is a *control layer* (deadline-aware admission + periodic-session
scheduling + KV-budget management) that sits on top of an execution backend. Any
backend that can (a) hold per-session context and (b) execute one frame's worth of
decode for a batch of sessions, reporting the measured wall-clock latency, can be
driven by Metronome. We ship two backends:

  * ``VLLMBackend``  — real models on vLLM (PagedAttention, prefix caching).
  * ``NativeBackend`` — the architecture-faithful timing engine (``metronome.engine``).

An SGLang backend (the plan's eventual substrate, via its persistent-sequence
primitive) is a drop-in: implement this same interface.
"""
from __future__ import annotations

from typing import Optional, Protocol, Sequence, runtime_checkable


@runtime_checkable
class Backend(Protocol):
    """Minimal contract a serving backend must satisfy for Metronome to drive it.

    Two faces, kept deliberately separate:

      * the **synthetic timing** face (``add_session``/``step``) — feeds shaped token
        streams through the real engine to measure the batched per-frame cost; used by
        the cost-model / capacity experiments, NOT by the production serving worker.
      * the **serving** face (:class:`ServingBackend`) — real multimodal input in, real
        decoded tokens out; this is what the gRPC worker + Realtime API drive.

    A production adapter implements both; an experiment-only backend may implement only
    the first. The serving worker should depend only on :class:`ServingBackend`.
    """

    # --- model facts the cost model / admission test need --------------------
    @property
    def kv_bytes_per_token(self) -> int: ...
    @property
    def num_layers(self) -> int: ...
    @property
    def hbm_kv_bytes(self) -> float:
        """HBM available for KV (total - weights - workspace)."""
        ...

    # --- session lifecycle ---------------------------------------------------
    def add_session(self, sid: int, kv_budget_tokens: int) -> None:
        """Register a new persistent session (reserve its KV budget)."""
        ...

    def remove_session(self, sid: int) -> None:
        """Free a departed session's resources."""
        ...

    def context_len(self, sid: int) -> int:
        """Current resident context length (tokens) of a session."""
        ...

    # --- the frame tick ------------------------------------------------------
    def step(self, due_sids: Sequence[int], n_new: int) -> float:
        """Execute one frame: ingest ``n_new`` new tokens for each due session and
        decode, on the real backend. Returns the **measured wall-clock latency (ms)**
        of the batched tick. Advances each session's context."""
        ...


@runtime_checkable
class ServingBackend(Protocol):
    """The REAL serving contract — what the gRPC worker and the OpenAI-Realtime API
    drive end-to-end. Distinct from the synthetic timing :class:`Backend` face above.

    Every method here takes/returns real data (audio PCM, PIL images, token ids,
    decoded text). Implementations MUST fail loud on malformed input and MUST be safe
    to call concurrently across distinct ``sid`` values within one frame.
    """

    # --- per-session input staging ------------------------------------------
    def set_input(self, sid: int, audio=None, images=None, text: str = "",
                  max_tokens: int = 128) -> None:
        """Stage a real multimodal user turn (audio + image(s) + text) for ``sid``,
        consumed on the next streaming step. Must validate shapes/types and raise
        ``ValueError`` on malformed input."""
        ...

    # --- the streaming frame -------------------------------------------------
    def step_stream(self, due_sids: Sequence[int], max_steps: int = 1) -> float:
        """Advance real streaming generation by ``max_steps`` decode tokens over the
        due sessions; record per-session new tokens in ``last_outputs`` and finished
        sessions in ``just_finished``. Returns measured ms."""
        ...

    def fd_step(self, sid_audio: dict, tpt: int) -> float:
        """Continuous full-duplex frame: prefill each session's new audio window and
        decode ``tpt`` output tokens as one batched pass. Returns measured ms."""
        ...

    def is_finished(self, sid: int) -> bool:
        """Did ``sid``'s in-flight response end this frame?"""
        ...

    # --- output / lifecycle --------------------------------------------------
    def detokenize(self, token_ids) -> str:
        """Decode token ids to text (skipping special tokens)."""
        ...

    def abort(self, sid: int) -> None:
        """Cancel any in-flight request for ``sid`` (barge-in / disconnect)."""
        ...

    def remove_session(self, sid: int) -> None:
        """Free all per-session resources (aborting any in-flight request)."""
        ...

    def num_unfinished(self) -> int:
        """Engine in-flight request count (-1 if unknown)."""
        ...

    def shutdown(self) -> None:
        """Tear down the engine and free GPU memory."""
        ...
