# components/internal_knowledge/organization/heuristics/__init__.py
from typing import Dict, Hashable
from infra.quality_evaluator import HeuristicRuleFn
from components.internal_knowledge.schemas.information import Information
from components.internal_knowledge.schemas.source_uri import SourceScheme
from .code_rules import heuristic_code_and_file
from .general_rules import heuristic_chat, heuristic_web

DEFAULT_INFO_HEURISTIC_RULES: Dict[Hashable, HeuristicRuleFn[Information]] = {
    SourceScheme.REPO: heuristic_code_and_file,
    SourceScheme.FILE: heuristic_code_and_file,
    SourceScheme.CHAT: heuristic_chat,
    SourceScheme.HTTP: heuristic_web,
    SourceScheme.HTTPS: heuristic_web,
}

__all__ = [
    "DEFAULT_INFO_HEURISTIC_RULES",
    "heuristic_code_and_file",
    "heuristic_chat",
    "heuristic_web",
]
