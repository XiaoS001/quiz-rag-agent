from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from skills.registry import Skill

CHECK_CITATION_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "retrieved_results": {
            "type": "array",
            "items": {"type": "object"},
        },
    },
    "required": ["answer", "retrieved_results"],
}

_CITATION_PATTERN = re.compile(
    r"(?:\[|\u3010)\s*(?:Q|q)?[-_]?(\d+)\s*(?:\]|\u3011)"
    r"|(?<![A-Za-z0-9_])(?:Q|q)[-_]?(\d+)(?![A-Za-z0-9_])"
)


def _extract_result_id(result: Any) -> str | None:
    if isinstance(result, Mapping):
        for key in ("id", "question_id", "qid", "questionId"):
            value = result.get(key)
            if value is not None:
                return str(value)

        metadata = result.get("metadata")
        if isinstance(metadata, Mapping):
            for key in ("id", "question_id", "qid", "questionId"):
                value = metadata.get(key)
                if value is not None:
                    return str(value)

    for key in ("id", "question_id", "qid", "questionId"):
        value = getattr(result, key, None)
        if value is not None:
            return str(value)

    return None


def extract_citation_ids(answer: str) -> list[str]:
    citations: list[str] = []
    seen: set[str] = set()

    for match in _CITATION_PATTERN.finditer(answer):
        citation = next(group for group in match.groups() if group is not None)
        if citation not in seen:
            seen.add(citation)
            citations.append(citation)

    return citations


def check_citation(
    answer: str,
    retrieved_results: Iterable[Any],
) -> dict[str, Any]:
    citations = extract_citation_ids(answer)
    retrieved_ids = {
        result_id
        for result in retrieved_results
        if (result_id := _extract_result_id(result)) is not None
    }
    invalid_citations = [
        citation for citation in citations if citation not in retrieved_ids
    ]

    return {
        "ok": not invalid_citations,
        "citations": citations,
        "retrieved_ids": sorted(retrieved_ids),
        "invalid_citations": invalid_citations,
    }


def create_check_citation_skill() -> Skill:
    return Skill(
        name="check_citation",
        description="Check that answer citations point to ids present in retrieved results.",
        run=check_citation,
        input_schema=CHECK_CITATION_INPUT_SCHEMA,
    )


skill = create_check_citation_skill()
