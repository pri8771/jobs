import re
from typing import Literal
from pydantic import BaseModel

class InjectionSignal(BaseModel):
    pattern_id: str
    excerpt: str
    severity: Literal["LOW", "HIGH"]
    context: str

PATTERNS = [
    ("override", re.compile(r"ignore (?:all )?(?:previous|prior|above) instructions|disregard .* rules", re.IGNORECASE), "HIGH"),
    ("role_hijack", re.compile(r"you are (?:now )?an? (?:ai|assistant|agent)", re.IGNORECASE), "LOW"),
    ("exfil", re.compile(r"(?:print|reveal|send) .* (?:token|password|secret|api key)", re.IGNORECASE), "HIGH"),
    ("authority", re.compile(r"(?:mark|set|treat) .* as (?:submitted|approved|authorized|verified)", re.IGNORECASE), "HIGH"),
    ("hidden_marker", re.compile(r"<!--.*(?:instruction|assistant).*-->|system:", re.IGNORECASE), "LOW")
]

def detect_prompt_injection_signals(text: str, *, context: str) -> list[InjectionSignal]:
    signals = []
    for pattern_id, regex, severity in PATTERNS:
        for match in regex.finditer(text):
            excerpt = text[max(0, match.start() - 30):min(len(text), match.end() + 30)]
            if len(excerpt) > 120:
                excerpt = excerpt[:117] + "..."
            signals.append(
                InjectionSignal(
                    pattern_id=pattern_id,
                    excerpt=excerpt,
                    severity=severity,
                    context=context
                )
            )
    return signals
