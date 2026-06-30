"""
Prompt Quality Scorer.

Scores a prompt on five weighted dimensions without any external dependencies.
All scoring is purely rule-based and heuristic.

Dimensions (weights):
  clarity       25%  – sentence structure, avg word length, action words
  specificity   25%  – prompt length, numbers/dates/names, technical terms
  completeness  20%  – role/context/task indicators, output format hints
  context       15%  – domain vocabulary density, background phrases
  actionability 15%  – action verb start, clear deliverable, measurable outcome

Final score = weighted average * 10  (0–100 scale)
Grade: A >= 85 | B >= 70 | C >= 55 | D >= 40 | F < 40
"""

import re
import string
from typing import Any


# ---------------------------------------------------------------------------
# Word lists / patterns used by the scorer
# ---------------------------------------------------------------------------

ACTION_WORDS: set[str] = {
    "analyze", "analyse", "build", "calculate", "classify", "compare",
    "compose", "create", "debug", "define", "describe", "design",
    "develop", "diagnose", "draft", "evaluate", "explain", "extract",
    "generate", "identify", "implement", "list", "optimize", "optimise",
    "outline", "produce", "provide", "recommend", "review", "solve",
    "summarize", "summarise", "translate", "write",
}

ROLE_INDICATORS: set[str] = {
    "you are", "act as", "acting as", "role of", "as an", "as a",
    "you're a", "you're an", "behave as", "imagine you are",
}

CONTEXT_INDICATORS: set[str] = {
    "context", "background", "given that", "assuming", "based on",
    "considering", "in the context of", "for the purpose of",
    "the situation is", "scenario",
}

TASK_INDICATORS: set[str] = {
    "task", "goal", "objective", "aim", "purpose", "requirement",
    "need", "want", "request", "please", "help me", "i need",
}

OUTPUT_FORMAT_HINTS: set[str] = {
    "format", "output", "response", "answer", "result", "list",
    "table", "bullet", "numbered", "paragraph", "section", "heading",
    "code", "json", "xml", "markdown", "summary", "report",
}

CONSTRAINT_WORDS: set[str] = {
    "constraint", "limit", "restrict", "avoid", "do not", "don't",
    "must", "should", "requirement", "rule", "only", "maximum",
    "minimum", "within", "without", "exclude", "include only",
}

TECHNICAL_TERMS: set[str] = {
    "algorithm", "api", "architecture", "authentication", "cache",
    "class", "database", "deployment", "endpoint", "framework",
    "function", "http", "interface", "library", "method", "module",
    "object", "parameter", "protocol", "query", "schema", "server",
    "service", "sql", "token", "variable", "webhook", "hypothesis",
    "analysis", "evaluation", "metrics", "optimization", "regression",
    "coefficient", "derivative", "integral", "matrix", "vector",
    "entropy", "probability", "distribution", "correlation",
}

BACKGROUND_PHRASES: list[str] = [
    "background", "context", "for example", "such as", "including",
    "specifically", "in particular", "notably", "previously",
    "currently", "recently", "historically", "typically", "generally",
]

DOMAIN_VOCABULARY: set[str] = TECHNICAL_TERMS | {
    "clinical", "diagnosis", "therapeutic", "legislation", "jurisprudence",
    "equilibrium", "catalyst", "photosynthesis", "neurological",
    "macroeconomics", "microeconomics", "litigation", "pedagogical",
}

MEASURABLE_WORDS: set[str] = {
    "percentage", "score", "rating", "rank", "number", "count",
    "frequency", "rate", "ratio", "proportion", "amount", "quantity",
    "metric", "kpi", "benchmark", "threshold", "target", "goal",
    "deadline", "timeline",
}


# ---------------------------------------------------------------------------
# PromptScorer
# ---------------------------------------------------------------------------

class PromptScorer:
    """Algorithmic prompt quality scorer."""

    WEIGHTS: dict[str, float] = {
        "clarity": 0.25,
        "specificity": 0.25,
        "completeness": 0.20,
        "context": 0.15,
        "actionability": 0.15,
    }

    GRADE_THRESHOLDS: list[tuple[float, str]] = [
        (85.0, "A"),
        (70.0, "B"),
        (55.0, "C"),
        (40.0, "D"),
        (0.0, "F"),
    ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, prompt: str) -> dict[str, Any]:
        """
        Score *prompt* across five dimensions.

        Returns
        -------
        dict with keys:
          score, clarity, specificity, completeness, context,
          actionability, grade
        """
        lower = prompt.lower()
        words = self._tokenize(prompt)
        word_count = len(words)

        clarity = self._score_clarity(prompt, lower, words, word_count)
        specificity = self._score_specificity(prompt, lower, words, word_count)
        completeness = self._score_completeness(lower)
        context_score = self._score_context(lower, words)
        actionability = self._score_actionability(prompt, lower, words)

        # Weighted average on 0-10 scale, then multiply by 10 -> 0-100
        weighted = (
            clarity * self.WEIGHTS["clarity"]
            + specificity * self.WEIGHTS["specificity"]
            + completeness * self.WEIGHTS["completeness"]
            + context_score * self.WEIGHTS["context"]
            + actionability * self.WEIGHTS["actionability"]
        )
        final_score = round(min(weighted * 10, 100.0), 2)

        return {
            "score": final_score,
            "clarity": round(clarity, 2),
            "specificity": round(specificity, 2),
            "completeness": round(completeness, 2),
            "context": round(context_score, 2),
            "actionability": round(actionability, 2),
            "grade": self._grade(final_score),
        }

    # ------------------------------------------------------------------
    # Dimension scorers (each returns a float 0-10)
    # ------------------------------------------------------------------

    def _score_clarity(
        self,
        prompt: str,
        lower: str,
        words: list[str],
        word_count: int,
    ) -> float:
        """
        Clarity – how easy is the prompt to understand?

        Sub-criteria:
          - Reasonable average sentence length (5–20 words ideal)
          - Avg word length (3–8 chars ideal)
          - Presence of direct question marks or action words (+bonus)
          - Not too short (< 5 words) or too long (> 500 words)
        """
        if word_count < 3:
            return 1.0

        score = 0.0

        # Average word length heuristic (ideal 4-7 chars)
        avg_word_len = sum(len(w) for w in words) / max(word_count, 1)
        if 4 <= avg_word_len <= 7:
            score += 3.0
        elif 3 <= avg_word_len < 4 or 7 < avg_word_len <= 9:
            score += 2.0
        else:
            score += 1.0

        # Sentence structure – number of sentences vs word count
        sentences = re.split(r"[.!?]+", prompt)
        sentence_count = max(len([s for s in sentences if s.strip()]), 1)
        avg_sent_len = word_count / sentence_count
        if 5 <= avg_sent_len <= 25:
            score += 3.0
        elif 3 <= avg_sent_len < 5 or 25 < avg_sent_len <= 40:
            score += 2.0
        else:
            score += 1.0

        # Action words presence
        action_hits = sum(1 for w in words if w.lower() in ACTION_WORDS)
        if action_hits >= 2:
            score += 2.5
        elif action_hits == 1:
            score += 1.5
        else:
            score += 0.5

        # Question mark or imperative tone
        if "?" in prompt:
            score += 1.0
        if any(w in lower for w in {"please", "provide", "ensure", "make sure"}):
            score += 0.5

        return min(score, 10.0)

    def _score_specificity(
        self,
        prompt: str,
        lower: str,
        words: list[str],
        word_count: int,
    ) -> float:
        """
        Specificity – how concrete and detailed is the prompt?

        Sub-criteria:
          - Prompt length (more detail = better, up to a point)
          - Numbers, dates, percentages present
          - Proper nouns / names present (heuristic: title-case words)
          - Technical terms present
        """
        score = 0.0

        # Length scoring
        if word_count >= 80:
            score += 4.0
        elif word_count >= 40:
            score += 3.0
        elif word_count >= 20:
            score += 2.0
        elif word_count >= 10:
            score += 1.5
        else:
            score += 0.5

        # Numbers / dates / percentages
        has_numbers = bool(re.search(r"\b\d+\b", prompt))
        has_percentage = "%" in prompt
        has_date = bool(
            re.search(
                r"\b(january|february|march|april|may|june|july|august|"
                r"september|october|november|december|\d{4}|\d{1,2}/\d{1,2})\b",
                lower,
            )
        )
        specificity_boost = sum([has_numbers, has_percentage, has_date])
        score += min(specificity_boost * 1.5, 3.0)

        # Technical terms
        tech_hits = sum(1 for w in words if w.lower() in TECHNICAL_TERMS)
        if tech_hits >= 3:
            score += 2.0
        elif tech_hits >= 1:
            score += 1.0

        # Proper nouns (title-case mid-sentence heuristic)
        tokens = prompt.split()
        proper_nouns = [
            t for i, t in enumerate(tokens)
            if i > 0 and t[0].isupper() and t.strip(string.punctuation).isalpha()
        ]
        if len(proper_nouns) >= 2:
            score += 1.0
        elif len(proper_nouns) == 1:
            score += 0.5

        return min(score, 10.0)

    def _score_completeness(self, lower: str) -> float:
        """
        Completeness – does the prompt include all structural elements?

        Sub-criteria:
          - Role / persona indicators
          - Context / background indicators
          - Task / goal indicators
          - Output format hints
          - Constraints or requirements
        """
        score = 0.0

        has_role = any(ind in lower for ind in ROLE_INDICATORS)
        has_context = any(ind in lower for ind in CONTEXT_INDICATORS)
        has_task = any(ind in lower for ind in TASK_INDICATORS)
        has_output = any(hint in lower for hint in OUTPUT_FORMAT_HINTS)
        has_constraint = any(cw in lower for cw in CONSTRAINT_WORDS)

        # Score each element
        score += 2.5 if has_role else 0.0
        score += 2.0 if has_context else 0.0
        score += 2.0 if has_task else 0.5  # small baseline even without explicit task
        score += 2.0 if has_output else 0.0
        score += 1.5 if has_constraint else 0.0

        return min(score, 10.0)

    def _score_context(self, lower: str, words: list[str]) -> float:
        """
        Context – does the prompt provide sufficient background?

        Sub-criteria:
          - Domain vocabulary density
          - Background/context phrases present
          - Prompt references "above", "following", "below" (self-referential)
        """
        score = 0.0

        word_count = max(len(words), 1)

        # Domain vocabulary density
        domain_hits = sum(1 for w in words if w.lower() in DOMAIN_VOCABULARY)
        density = domain_hits / word_count
        if density >= 0.08:
            score += 4.0
        elif density >= 0.04:
            score += 3.0
        elif density >= 0.02:
            score += 2.0
        elif domain_hits >= 1:
            score += 1.0

        # Background phrases
        bg_hits = sum(1 for p in BACKGROUND_PHRASES if p in lower)
        if bg_hits >= 3:
            score += 3.0
        elif bg_hits >= 2:
            score += 2.0
        elif bg_hits >= 1:
            score += 1.0

        # Self-referential context pointers
        if any(ref in lower for ref in {"above", "below", "following", "herein", "aforementioned"}):
            score += 1.5

        # Long prompt implies more context
        if word_count >= 100:
            score += 1.5
        elif word_count >= 50:
            score += 0.5

        return min(score, 10.0)

    def _score_actionability(
        self,
        prompt: str,
        lower: str,
        words: list[str],
    ) -> float:
        """
        Actionability – can the LLM produce a concrete, useful response?

        Sub-criteria:
          - Starts with an action verb
          - Contains a clear deliverable noun
          - Mentions a measurable / concrete outcome
          - Has at least one specific constraint or scope limiter
        """
        score = 0.0

        # Starts with action verb (first non-stopword word)
        first_word = words[0].lower().strip(string.punctuation) if words else ""
        if first_word in ACTION_WORDS:
            score += 3.0
        elif any(lower.startswith(aw) for aw in ACTION_WORDS):
            score += 2.0

        # Clear deliverable – output format hints near the end
        tail = lower[-200:]  # last 200 chars
        deliverable_hits = sum(1 for hint in OUTPUT_FORMAT_HINTS if hint in tail)
        if deliverable_hits >= 2:
            score += 2.5
        elif deliverable_hits == 1:
            score += 1.5

        # Measurable outcome words
        measure_hits = sum(1 for mw in MEASURABLE_WORDS if mw in lower)
        if measure_hits >= 2:
            score += 2.5
        elif measure_hits == 1:
            score += 1.5

        # Scope / constraint limiter
        constraint_hits = sum(1 for cw in CONSTRAINT_WORDS if cw in lower)
        if constraint_hits >= 2:
            score += 2.0
        elif constraint_hits == 1:
            score += 1.0

        return min(score, 10.0)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _tokenize(self, text: str) -> list[str]:
        """Simple whitespace tokeniser that strips punctuation."""
        return [
            w.strip(string.punctuation)
            for w in text.split()
            if w.strip(string.punctuation)
        ]

    def _grade(self, score: float) -> str:
        for threshold, grade in self.GRADE_THRESHOLDS:
            if score >= threshold:
                return grade
        return "F"
