"""
AMPOA Engine - Adaptive Multi-stage Prompt Optimization Algorithm.

A fully rule-based, algorithmic pipeline that transforms a raw user prompt into a
well-structured, model-agnostic "universal prompt" without any external LLM calls.

Stages:
  1. clean_prompt       - normalise whitespace / punctuation
  2. detect_intent      - keyword-based intent classification
  3. detect_domain      - keyword-based domain classification
  4. extract_entities   - stopword-filtered noun/concept extraction
  5. enrich_context     - add intent+domain framing phrases
  6. expand_prompt      - add clarity/completeness directives
  7. structure_prompt   - format into Role/Task/Context/Constraints/Output
"""

import re
import string
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STOPWORDS: set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "through", "during",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "shall", "can", "need", "dare", "ought", "used", "it", "its", "this",
    "that", "these", "those", "i", "me", "my", "we", "our", "you", "your",
    "he", "she", "they", "them", "their", "what", "which", "who", "when",
    "where", "why", "how", "all", "each", "both", "few", "more", "most",
    "other", "some", "such", "no", "not", "only", "same", "so", "than",
    "too", "very", "just", "as", "if", "then", "because", "while", "after",
    "before", "also", "any", "one", "two", "get", "make", "give", "see",
    "know", "think", "come", "go", "take", "use", "find", "want", "tell",
    "call", "try", "ask", "need", "feel", "become", "leave", "put", "mean",
    "keep", "let", "begin", "seem", "show", "hear", "play", "run", "move",
    "live", "believe", "hold", "bring", "happen", "write", "provide", "set",
    "change", "lead", "understand", "watch", "follow", "stop", "create",
    "speak", "read", "spend", "grow", "open", "walk", "win", "offer", "remember",
    "love", "consider", "appear", "buy", "wait", "serve", "die", "send", "expect",
    "build", "stay", "fall", "cut", "reach", "kill", "remain", "suggest",
    "raise", "pass", "sell", "require", "report", "decide", "pull", "please",
    "include", "continue", "add", "specific", "based", "given", "related",
}

INTENT_KEYWORDS: dict[str, list[str]] = {
    "explain": [
        "explain", "what is", "what are", "describe", "definition",
        "how does", "how do", "clarify", "elaborate", "tell me about",
        "define", "meaning of",
    ],
    "generate": [
        "generate", "write", "draft", "compose", "produce", "create content",
        "write me", "come up with", "write a", "write an",
    ],
    "analyze": [
        "analyze", "analyse", "examine", "investigate", "review",
        "assess", "evaluate", "study", "break down", "deep dive",
    ],
    "summarize": [
        "summarize", "summarise", "summary", "tldr", "tl;dr",
        "key points", "main points", "brief overview", "condense", "shorten",
    ],
    "compare": [
        "compare", "contrast", "difference between", "versus", "vs",
        "pros and cons", "advantages and disadvantages", "which is better",
    ],
    "translate": [
        "translate", "convert to", "in spanish", "in french", "in german",
        "in japanese", "in chinese", "in arabic", "language",
    ],
    "debug": [
        "debug", "fix", "error", "bug", "issue", "problem", "not working",
        "broken", "troubleshoot", "why is", "why does", "failing",
    ],
    "create": [
        "create", "build", "design", "develop", "make", "construct",
        "implement", "set up", "architect", "code", "program",
    ],
    "evaluate": [
        "evaluate", "rate", "score", "judge", "critique", "feedback",
        "how good", "is it correct", "check", "validate", "verify",
    ],
}

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "technology": [
        "code", "programming", "software", "api", "database", "algorithm",
        "machine learning", "ai", "artificial intelligence", "web", "app",
        "python", "javascript", "java", "cloud", "server", "network",
        "cybersecurity", "data", "devops", "docker", "kubernetes", "react",
        "backend", "frontend", "function", "class", "object", "framework",
    ],
    "science": [
        "physics", "chemistry", "biology", "astronomy", "genetics",
        "evolution", "quantum", "molecule", "atom", "experiment",
        "hypothesis", "research", "scientific", "laboratory", "dna",
        "ecology", "climate", "geology", "neuroscience", "photosynthesis",
    ],
    "business": [
        "business", "marketing", "sales", "revenue", "profit", "startup",
        "strategy", "management", "finance", "investment", "roi", "kpi",
        "customer", "market", "brand", "entrepreneur", "product", "service",
        "b2b", "b2c", "growth", "monetize", "scaling", "stakeholder",
    ],
    "healthcare": [
        "health", "medical", "medicine", "doctor", "patient", "hospital",
        "disease", "treatment", "symptom", "diagnosis", "drug", "therapy",
        "clinical", "nurse", "surgery", "mental health", "pharmacy",
        "wellness", "nutrition", "exercise", "fitness", "diet",
    ],
    "education": [
        "education", "learning", "teaching", "student", "teacher", "school",
        "university", "course", "curriculum", "lesson", "study", "exam",
        "homework", "lecture", "classroom", "knowledge", "tutor", "grade",
    ],
    "creative_writing": [
        "story", "poem", "novel", "fiction", "character", "plot",
        "narrative", "creative", "write a story", "short story", "essay",
        "screenplay", "dialogue", "scene", "protagonist", "antagonist",
        "genre", "fantasy", "sci-fi", "horror", "romance", "thriller",
    ],
    "mathematics": [
        "math", "mathematics", "equation", "algebra", "calculus",
        "geometry", "statistics", "probability", "proof", "theorem",
        "formula", "integral", "derivative", "matrix", "vector", "number",
        "arithmetic", "fraction", "polynomial", "graph",
    ],
    "legal": [
        "law", "legal", "lawyer", "attorney", "contract", "regulation",
        "compliance", "court", "judge", "lawsuit", "rights", "legislation",
        "policy", "statute", "intellectual property", "patent", "copyright",
        "gdpr", "privacy", "liability", "clause",
    ],
}

CONTEXT_PHRASES: dict[str, dict[str, str]] = {
    "explain": {
        "technology": "You are explaining a technical concept to a developer audience.",
        "science": "You are explaining a scientific concept with accuracy and clarity.",
        "business": "You are explaining a business concept to a professional audience.",
        "healthcare": "You are explaining a medical or health concept clearly and responsibly.",
        "education": "You are explaining an educational concept to learners.",
        "creative_writing": "You are explaining a creative writing technique to an aspiring writer.",
        "mathematics": "You are explaining a mathematical concept step by step.",
        "legal": "You are explaining a legal concept in plain language (not legal advice).",
        "general": "You are providing a clear, thorough explanation.",
    },
    "generate": {
        "technology": "You are an expert software developer generating technical content.",
        "science": "You are a scientist generating evidence-based content.",
        "business": "You are a business professional generating strategic content.",
        "healthcare": "You are a healthcare professional generating responsible medical content.",
        "education": "You are an educator generating instructional content.",
        "creative_writing": "You are a creative writer generating engaging narrative content.",
        "mathematics": "You are a mathematician generating precise mathematical content.",
        "legal": "You are generating content on legal topics (not legal advice).",
        "general": "You are generating high-quality, accurate content.",
    },
    "analyze": {
        "technology": "You are a technical analyst performing a thorough technical analysis.",
        "science": "You are a researcher conducting a rigorous scientific analysis.",
        "business": "You are a business analyst providing strategic insights.",
        "healthcare": "You are a medical professional analyzing health-related information.",
        "education": "You are an educator analyzing learning outcomes and methods.",
        "creative_writing": "You are a literary critic analyzing creative works.",
        "mathematics": "You are a mathematician performing a systematic mathematical analysis.",
        "legal": "You are conducting a careful analysis of legal concepts.",
        "general": "You are performing a comprehensive, objective analysis.",
    },
}

EXPAND_DIRECTIVES: dict[str, list[str]] = {
    "explain": [
        "Please provide a clear and complete explanation.",
        "Include real-world examples where applicable.",
        "Use simple language where possible while maintaining accuracy.",
        "Structure the explanation from basic to advanced concepts.",
    ],
    "generate": [
        "Please produce complete, polished output.",
        "Ensure the content is original and high-quality.",
        "Include all necessary details without being redundant.",
        "Follow best practices and conventions for this type of content.",
    ],
    "analyze": [
        "Please provide a thorough, balanced analysis.",
        "Support your points with evidence and reasoning.",
        "Identify key strengths, weaknesses, and implications.",
        "Present findings in a logical, structured manner.",
    ],
    "summarize": [
        "Capture all key points without losing important details.",
        "Keep the summary concise and easy to read.",
        "Prioritize the most important information.",
        "Maintain the original meaning and intent.",
    ],
    "compare": [
        "Address both similarities and differences clearly.",
        "Use a structured comparison format.",
        "Provide a final recommendation or conclusion where appropriate.",
        "Include specific examples to illustrate each point.",
    ],
    "translate": [
        "Ensure the translation is accurate and natural-sounding.",
        "Preserve the original tone and intent.",
        "Note any culturally specific nuances where relevant.",
    ],
    "debug": [
        "Identify the root cause of the issue.",
        "Provide a step-by-step solution.",
        "Explain why the problem occurred.",
        "Suggest best practices to prevent similar issues.",
    ],
    "create": [
        "Provide a complete, working implementation.",
        "Follow industry best practices and standards.",
        "Include comments or documentation where appropriate.",
        "Consider edge cases and error handling.",
    ],
    "evaluate": [
        "Provide objective, constructive feedback.",
        "Use clear criteria for evaluation.",
        "Highlight both strengths and areas for improvement.",
        "Offer specific, actionable recommendations.",
    ],
    "other": [
        "Please provide a comprehensive and accurate response.",
        "Include examples if applicable.",
        "Be specific and thorough in your answer.",
    ],
}


# ---------------------------------------------------------------------------
# AMPOAEngine
# ---------------------------------------------------------------------------

class AMPOAEngine:
    """Adaptive Multi-stage Prompt Optimization Algorithm engine."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def optimize(self, raw_prompt: str) -> dict[str, Any]:
        """
        Run the full AMPOA pipeline on *raw_prompt*.

        Returns a dict containing every intermediate stage result plus the
        final ``universal_prompt``.
        """
        cleaned = self.clean_prompt(raw_prompt)
        intent = self.detect_intent(cleaned)
        domain = self.detect_domain(cleaned)
        entities = self.extract_entities(cleaned)
        enriched = self.enrich_context(cleaned, intent, domain)
        expanded = self.expand_prompt(enriched, intent)
        universal = self.structure_prompt(expanded, intent, domain, entities)

        return {
            "original_prompt": raw_prompt,
            "cleaned_prompt": cleaned,
            "intent": intent,
            "domain": domain,
            "entities": entities,
            "enriched_prompt": enriched,
            "expanded_prompt": expanded,
            "universal_prompt": universal,
        }

    # ------------------------------------------------------------------
    # Stage 1 – Clean
    # ------------------------------------------------------------------

    def clean_prompt(self, raw: str) -> str:
        """Remove extra whitespace, fix common punctuation issues, normalise text."""
        # Collapse runs of whitespace / newlines
        text = re.sub(r"\s+", " ", raw).strip()

        # Remove repeated punctuation (e.g. "???" -> "?", "!!!" -> "!")
        text = re.sub(r"([!?.]){2,}", r"\1", text)

        # Ensure sentence ends with a punctuation mark
        if text and text[-1] not in string.punctuation:
            text += "."

        # Fix common contractions / smart quotes
        text = text.replace("\u2019", "'").replace("\u2018", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')

        return text

    # ------------------------------------------------------------------
    # Stage 2 – Intent detection
    # ------------------------------------------------------------------

    def detect_intent(self, text: str) -> str:
        """Classify the user's intent from a fixed set of categories."""
        lower = text.lower()
        scores: dict[str, int] = {intent: 0 for intent in INTENT_KEYWORDS}

        for intent, keywords in INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw in lower:
                    scores[intent] += 1

        best_intent = max(scores, key=lambda k: scores[k])
        if scores[best_intent] == 0:
            return "other"
        return best_intent

    # ------------------------------------------------------------------
    # Stage 3 – Domain detection
    # ------------------------------------------------------------------

    def detect_domain(self, text: str) -> str:
        """Classify the prompt's domain from a fixed set of categories."""
        lower = text.lower()
        scores: dict[str, int] = {domain: 0 for domain in DOMAIN_KEYWORDS}

        for domain, keywords in DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if kw in lower:
                    scores[domain] += 1

        best_domain = max(scores, key=lambda k: scores[k])
        if scores[best_domain] == 0:
            return "general"
        return best_domain

    # ------------------------------------------------------------------
    # Stage 4 – Entity extraction
    # ------------------------------------------------------------------

    def extract_entities(self, text: str) -> list[str]:
        """Extract meaningful nouns/concepts using simple stopword filtering."""
        # Remove punctuation and split
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        words = cleaned.split()

        # Filter: remove stopwords, very short tokens, and pure numbers
        entities: list[str] = []
        seen: set[str] = set()
        for word in words:
            if (
                word not in STOPWORDS
                and len(word) > 2
                and not word.isdigit()
                and word not in seen
            ):
                entities.append(word)
                seen.add(word)

        return entities[:20]  # cap at 20 entities

    # ------------------------------------------------------------------
    # Stage 5 – Context enrichment
    # ------------------------------------------------------------------

    def enrich_context(self, cleaned_prompt: str, intent: str, domain: str) -> str:
        """Prepend a context-framing sentence appropriate to intent + domain."""
        intent_map = CONTEXT_PHRASES.get(intent, CONTEXT_PHRASES.get("explain", {}))
        context_sentence = intent_map.get(domain, intent_map.get("general", ""))

        if context_sentence:
            return f"{context_sentence}\n\n{cleaned_prompt}"
        return cleaned_prompt

    # ------------------------------------------------------------------
    # Stage 6 – Prompt expansion
    # ------------------------------------------------------------------

    def expand_prompt(self, enriched_prompt: str, intent: str) -> str:
        """Add clarity and completeness directives based on the detected intent."""
        directives = EXPAND_DIRECTIVES.get(intent, EXPAND_DIRECTIVES["other"])
        directive_block = "\n".join(f"- {d}" for d in directives)
        return f"{enriched_prompt}\n\nAdditional requirements:\n{directive_block}"

    # ------------------------------------------------------------------
    # Stage 7 – Prompt structuring
    # ------------------------------------------------------------------

    def structure_prompt(
        self,
        expanded_prompt: str,
        intent: str,
        domain: str,
        entities: list[str],
    ) -> str:
        """Format the prompt into a well-structured Role/Task/Context/Constraints/Output template."""
        # Derive a concise role description
        role = self._build_role(intent, domain)

        # Constraints depend on domain
        constraints = self._build_constraints(domain)

        # Output format guidance depends on intent
        output_format = self._build_output_format(intent)

        # Entities as comma-separated string for context section
        entity_str = ", ".join(entities[:10]) if entities else "general concepts"

        structured = (
            f"## Role\n{role}\n\n"
            f"## Task\n{expanded_prompt}\n\n"
            f"## Context\nKey concepts and entities involved: {entity_str}\n"
            f"Domain: {domain.replace('_', ' ').title()}\n\n"
            f"## Constraints\n{constraints}\n\n"
            f"## Output Format\n{output_format}"
        )
        return structured

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_role(self, intent: str, domain: str) -> str:
        domain_label = domain.replace("_", " ").title()
        intent_roles: dict[str, str] = {
            "explain": f"Expert {domain_label} educator and communicator",
            "generate": f"Expert {domain_label} content creator",
            "analyze": f"Senior {domain_label} analyst",
            "summarize": f"Expert {domain_label} summarizer",
            "compare": f"Expert {domain_label} consultant",
            "translate": "Professional translator with domain expertise",
            "debug": f"Senior {domain_label} troubleshooter and debugger",
            "create": f"Expert {domain_label} developer and architect",
            "evaluate": f"Expert {domain_label} evaluator and reviewer",
            "other": f"Expert {domain_label} assistant",
        }
        return intent_roles.get(intent, f"Expert {domain_label} assistant")

    def _build_constraints(self, domain: str) -> str:
        base = (
            "- Provide accurate, well-researched information.\n"
            "- Be concise yet thorough.\n"
            "- Avoid unnecessary filler or repetition.\n"
            "- Cite assumptions where relevant."
        )
        domain_extras: dict[str, str] = {
            "healthcare": "\n- Do not provide specific medical diagnoses or personalised medical advice.",
            "legal": "\n- Do not provide specific legal advice; recommend consulting a qualified lawyer.",
            "technology": "\n- Prefer modern best practices and well-supported solutions.",
            "mathematics": "\n- Show all working/steps clearly.",
            "creative_writing": "\n- Adhere to the requested genre/tone/style.",
        }
        return base + domain_extras.get(domain, "")

    def _build_output_format(self, intent: str) -> str:
        formats: dict[str, str] = {
            "explain": (
                "- Use clear prose with headings for each major concept.\n"
                "- Include at least one concrete example.\n"
                "- End with a brief summary."
            ),
            "generate": (
                "- Produce the complete requested content.\n"
                "- Use appropriate formatting (headings, lists, code blocks) as needed.\n"
                "- Do not truncate the output."
            ),
            "analyze": (
                "- Structure as: Overview → Key Findings → Implications → Conclusion.\n"
                "- Use bullet points for findings.\n"
                "- Include a final summary paragraph."
            ),
            "summarize": (
                "- Present as a concise bullet-point list of key points.\n"
                "- Follow with a one-paragraph summary.\n"
                "- Keep total length proportional to the source."
            ),
            "compare": (
                "- Use a clear comparison structure (e.g., table or side-by-side sections).\n"
                "- Address each dimension separately.\n"
                "- Provide a final recommendation or verdict."
            ),
            "translate": (
                "- Provide the translated text in full.\n"
                "- Note any idiomatic differences or cultural nuances."
            ),
            "debug": (
                "- Identify the root cause clearly.\n"
                "- Provide a step-by-step fix.\n"
                "- Include corrected code or commands where applicable.\n"
                "- Explain how to verify the fix."
            ),
            "create": (
                "- Provide complete, runnable code or artefacts.\n"
                "- Include inline comments explaining key decisions.\n"
                "- List any dependencies or prerequisites.\n"
                "- Describe how to test or verify the output."
            ),
            "evaluate": (
                "- Use a structured rubric with clear scoring criteria.\n"
                "- Provide a score or grade where appropriate.\n"
                "- Balance positive feedback with constructive criticism.\n"
                "- End with prioritised improvement recommendations."
            ),
            "other": (
                "- Present information in a logical, readable structure.\n"
                "- Use headings and bullet points where helpful.\n"
                "- Be thorough but avoid unnecessary verbosity."
            ),
        }
        return formats.get(intent, formats["other"])
