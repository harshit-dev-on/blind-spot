"""Agent Skills Registry implementing Progressive Disclosure and dynamic discovery.

Follows the open Agent Skills specification (standardized under the Linux Foundation / Agentic AI Foundation).
Implements 3-tier progressive disclosure:
- Tier 1: Discovery (lightweight metadata catalog ~50 tokens/skill)
- Tier 2: Activation (on-demand loading of full SKILL.md body)
- Tier 3: Execution (lazy loading of references/, scripts/, assets/, examples/)
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from blindspot.skills.manager import (
    SkillMetadata,
    get_bundled_skills_dir,
    parse_skill_file,
)


@dataclass
class SkillSummary:
    """Tier 1: Lightweight metadata for initial context discovery (~50 tokens)."""

    name: str
    description: str
    version: str
    skill_dir: Path
    keywords: Set[str] = field(default_factory=set)


class SkillRegistry:
    """Registry coordinating discovery, progressive disclosure, and matching of Agent Skills."""

    # Common command aliases mapping short names to full skill identifiers
    SLASH_ALIASES: Dict[str, str] = {
        "ux": "blindspot-ux-audit",
        "audit": "blindspot-ux-audit",
        "ux-audit": "blindspot-ux-audit",
        "wcag": "blindspot-wcag-audit",
        "a11y": "blindspot-wcag-audit",
        "accessibility": "blindspot-wcag-audit",
        "verify": "blindspot-verify-fix",
        "verify-fix": "blindspot-verify-fix",
        "regression": "blindspot-verify-fix",
        "persona": "blindspot-persona-designer",
        "personas": "blindspot-persona-designer",
        "ecommerce": "blindspot-ecommerce-audit",
        "mobile": "blindspot-mobile-audit",
        "tracker": "blindspot-task-tracker",
        "task-tracker": "blindspot-task-tracker",
        "step-gate": "blindspot-task-tracker",
        "context": "blindspot-website-context",
        "website-context": "blindspot-website-context",
    }

    def __init__(self, search_paths: Optional[List[Path]] = None) -> None:
        self.search_paths = search_paths or self._default_search_paths()
        self._summaries: Dict[str, SkillSummary] = {}
        self._cache: Dict[str, SkillMetadata] = {}
        self.load()

    def _default_search_paths(self) -> List[Path]:
        """Collect standard skill search directories."""
        paths = [get_bundled_skills_dir()]
        cwd = Path.cwd()
        paths.append(cwd / ".agents" / "skills")
        paths.append(cwd / ".github" / "skills")
        return [p for p in paths if p.exists() and p.is_dir()]

    def load(self) -> int:
        """Discover all available SKILL.md files and populate Tier 1 summaries."""
        self._summaries.clear()
        self._cache.clear()

        for base_path in self.search_paths:
            if not base_path.is_dir():
                continue
            for item in sorted(base_path.iterdir()):
                if item.is_dir() and (item / "SKILL.md").is_file():
                    skill_file = item / "SKILL.md"
                    try:
                        meta = parse_skill_file(skill_file)
                        words = set(re.findall(r"[a-z0-9]+", f"{meta.name} {meta.description}".lower()))
                        summary = SkillSummary(
                            name=meta.name,
                            description=meta.description,
                            version=meta.version,
                            skill_dir=item,
                            keywords=words,
                        )
                        self._summaries[meta.name] = summary
                        self._cache[meta.name] = meta
                    except Exception:
                        continue

        return len(self._summaries)

    def list_summaries(self) -> List[SkillSummary]:
        """Return Tier 1 metadata summaries for all registered skills."""
        return list(self._summaries.values())

    def get_skill(self, name_or_alias: str) -> Optional[SkillMetadata]:
        """Tier 2: Retrieve full skill metadata and instructions, resolving aliases."""
        clean = name_or_alias.strip().lower()
        canonical_name = self.SLASH_ALIASES.get(clean, clean)

        if canonical_name in self._cache:
            return self._cache[canonical_name]

        summary = self._summaries.get(canonical_name)
        if summary:
            skill_file = summary.skill_dir / "SKILL.md"
            meta = parse_skill_file(skill_file)
            self._cache[canonical_name] = meta
            return meta

        return None

    def get_skill_resource(
        self, skill_name: str, resource_subpath: str
    ) -> Optional[str]:
        """Tier 3: Lazy-load sub-resources (references/, scripts/, assets/, examples/)."""
        skill = self.get_skill(skill_name)
        if not skill or not skill.skill_path:
            return None

        target = (skill.skill_path.parent / resource_subpath).resolve()
        parent = skill.skill_path.parent.resolve()

        # Prevent directory traversal
        try:
            target.relative_to(parent)
        except ValueError:
            return None

        if target.is_file():
            try:
                return target.read_text(encoding="utf-8")
            except Exception:
                return None

        return None

    def try_parse_slash_command(
        self, user_input: str
    ) -> Tuple[Optional[SkillMetadata], str]:
        """Detect and parse slash commands like '/wcag test contrast'."""
        text = user_input.strip()
        if not text.startswith("/"):
            return None, user_input

        parts = text[1:].split(maxsplit=1)
        command_name = parts[0].lower()
        remaining_text = parts[1] if len(parts) > 1 else ""

        skill = self.get_skill(command_name)
        return skill, remaining_text

    def find_matches(
        self, query: str, min_score: float = 0.2
    ) -> List[Tuple[SkillMetadata, float]]:
        """Score and rank skills based on query keyword overlap."""
        query_words = set(re.findall(r"[a-z0-9]+", query.lower()))
        if not query_words:
            return []

        scored: List[Tuple[SkillMetadata, float]] = []

        for name, summary in self._summaries.items():
            intersection = query_words.intersection(summary.keywords)
            if not intersection:
                continue

            # Prioritize matches in skill name
            name_parts = set(name.split("-"))
            name_hits = query_words.intersection(name_parts)

            score = (len(intersection) / len(query_words)) * 0.7 + (len(name_hits) * 0.3)
            score = min(1.0, score)

            if score >= min_score:
                skill = self.get_skill(name)
                if skill:
                    scored.append((skill, round(score, 2)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def find_best_match(self, query: str, min_score: float = 0.3) -> Optional[SkillMetadata]:
        """Return the highest-scoring matching skill or None."""
        matches = self.find_matches(query, min_score=min_score)
        return matches[0][0] if matches else None
