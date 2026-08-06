"""LLM-driven user simulator + NL-assertion judge for tau-interact-mm.

Both are backed by a local, OpenAI-compatible vLLM server (no external API, nothing
leaves the box). The simulator plays a goal-directed user talking by voice to an
assistant that can see an image; it emits short spoken-style turns and decides when the
goal is met. The judge scores tool-free correctness (tau2's COMMUNICATE + NL_ASSERTION).
"""
from __future__ import annotations

import json
import re


def _client(base_url, api_key="x"):
    from openai import OpenAI
    return OpenAI(base_url=base_url, api_key=api_key)


def _chat(client, model, messages, max_tokens=160, temperature=0.7):
    # Disable Qwen3 thinking so the model emits the requested JSON directly (a <think>
    # block breaks JSON parsing and leaks reasoning into the spoken utterance).
    r = client.chat.completions.create(
        model=model, messages=messages, max_tokens=max_tokens, temperature=temperature,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    return r.choices[0].message.content or ""


def _extract_json(s: str):
    s = re.sub(r"<think>.*?</think>", " ", s or "", flags=re.S)   # strip any reasoning
    s = re.sub(r"</?think>", " ", s)
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return None


class UserSimulator:
    """One instance per task. Generates the next user utterance given the dialogue."""

    SYS = (
        "You are role-playing a USER talking BY VOICE to an AI assistant that can SEE an "
        "image you are both looking at and HEAR you. Stay in character. Speak naturally and "
        "briefly (one short sentence), as a person would out loud. Pursue your goal across a "
        "few turns, reacting to what the assistant says. Do NOT describe the image yourself — "
        "you want the assistant to tell you. When your goal is satisfied (or clearly cannot "
        "be), end politely.\n"
        "Respond ONLY as compact JSON: {\"utterance\": \"<what you say out loud>\", "
        "\"done\": <true|false>}.")

    def __init__(self, base_url, model, goal, persona="a curious everyday user"):
        self.client = _client(base_url)
        self.model = model
        self.goal = goal
        self.persona = persona
        self.turns = []        # list of (speaker, text)

    def first(self):
        return self._step(opening=True)

    def reply(self, agent_text):
        self.turns.append(("assistant", agent_text))
        return self._step(opening=False)

    def _step(self, opening):
        hist = "\n".join(f"{s}: {t}" for s, t in self.turns) or "(no turns yet)"
        prompt = (f"Your persona: {self.persona}\nYour goal: {self.goal}\n\n"
                  f"Conversation so far:\n{hist}\n\n"
                  + ("Say your FIRST line to open the conversation toward your goal."
                     if opening else "Say your next line.")
                  + " Remember: ONLY JSON {\"utterance\":..., \"done\":...}.")
        out = _chat(self.client, self.model,
                    [{"role": "system", "content": self.SYS},
                     {"role": "user", "content": prompt}], max_tokens=120, temperature=0.7)
        obj = _extract_json(out) or {"utterance": out.strip()[:200], "done": False}
        utt = str(obj.get("utterance", "")).strip() or "Could you help me?"
        self.turns.append(("user", utt))
        return utt, bool(obj.get("done", False))


def judge_assertion(base_url, model, assertion: str, transcript: str) -> bool:
    """tau2 NL_ASSERTION: is the assertion true given the assistant's transcript?"""
    client = _client(base_url)
    out = _chat(client, model, [
        {"role": "system", "content": "You are a strict evaluator. Given an assistant's "
         "dialogue transcript and an assertion about it, answer if the assertion is TRUE. "
         "Respond ONLY as JSON: {\"true\": <true|false>}."},
        {"role": "user", "content": f"Transcript:\n{transcript}\n\nAssertion: {assertion}"}],
        max_tokens=20, temperature=0.0)
    obj = _extract_json(out) or {}
    return bool(obj.get("true", False))


def communicate_ok(facts, transcript: str) -> list[bool]:
    """tau2 COMMUNICATE: each required fact appears (normalized substring) in transcript."""
    t = re.sub(r"[^\w\s]", " ", (transcript or "").lower())
    t = " ".join(t.split())
    res = []
    for f in facts:
        fn = " ".join(re.sub(r"[^\w\s]", " ", f.lower()).split())
        res.append(fn in t)
    return res
