"""
MAPT Engine - Model-Adaptive Prompt Translation.

Transforms a universal (model-agnostic) prompt into a version optimised for
a specific LLM's preferred input style.  All transformations are purely
rule-based string operations — no external LLM calls are made.

Supported targets:
  - claude     : XML tags, structured thinking, step-by-step reasoning
  - chatgpt    : numbered steps, explicit role assignment, structured sections
  - gemini     : concise, direct, bold markdown headers, bullet points
  - deepseek   : technical precision, markdown code-block formatting hints
"""

import re


class MAPTEngine:
    """Model-Adaptive Prompt Translation engine."""

    def translate(self, universal_prompt: str, target_llm: str) -> str:
        """
        Adapt *universal_prompt* for *target_llm*.

        Parameters
        ----------
        universal_prompt : str
            The structured universal prompt produced by AMPOAEngine.
        target_llm : str
            One of "claude", "chatgpt", "gemini", "deepseek".

        Returns
        -------
        str
            The LLM-adapted prompt string.
        """
        adapter = getattr(self, f"_adapt_{target_llm.lower()}", None)
        if adapter is None:
            return universal_prompt
        return adapter(universal_prompt)

    # ------------------------------------------------------------------
    # Private adapters
    # ------------------------------------------------------------------

    def _adapt_claude(self, prompt: str) -> str:
        """
        Claude adapter.

        Preferences:
        - XML tag structure for clear section delineation
        - Explicit "think step by step" reasoning directive
        - Warm, thoughtful framing
        """
        # Extract named sections from the structured universal prompt
        sections = self._parse_sections(prompt)

        role = sections.get("Role", "an expert assistant")
        task = sections.get("Task", prompt)
        context = sections.get("Context", "")
        constraints = sections.get("Constraints", "")
        output_format = sections.get("Output Format", "")

        adapted = (
            f"<role>\n{role}\n</role>\n\n"
            f"<task>\n{task.strip()}\n</task>\n\n"
        )

        if context:
            adapted += f"<context>\n{context.strip()}\n</context>\n\n"

        if constraints:
            adapted += f"<constraints>\n{constraints.strip()}\n</constraints>\n\n"

        if output_format:
            adapted += f"<output_format>\n{output_format.strip()}\n</output_format>\n\n"

        adapted += (
            "<instructions>\n"
            "Think step by step before writing your final response.\n"
            "Reason carefully about the requirements and constraints above.\n"
            "Produce a thorough, well-organised answer.\n"
            "</instructions>"
        )

        return adapted

    def _adapt_chatgpt(self, prompt: str) -> str:
        """
        ChatGPT adapter.

        Preferences:
        - Explicit system-style role assignment at the top
        - Numbered steps for the task description
        - Clear section headers using ALL-CAPS labels
        - Polite, direct language
        """
        sections = self._parse_sections(prompt)

        role = sections.get("Role", "an expert assistant")
        task_raw = sections.get("Task", prompt)
        context = sections.get("Context", "")
        constraints = sections.get("Constraints", "")
        output_format = sections.get("Output Format", "")

        # Build numbered task steps from bullet lines or paragraphs
        task_numbered = self._to_numbered_steps(task_raw)

        adapted = f"You are {role}. Please provide a structured response with clear sections.\n\n"
        adapted += f"TASK:\n{task_numbered}\n"

        if context:
            adapted += f"\nCONTEXT:\n{context.strip()}\n"

        if constraints:
            adapted += f"\nCONSTRAINTS:\n{constraints.strip()}\n"

        if output_format:
            adapted += f"\nOUTPUT FORMAT:\n{output_format.strip()}\n"

        adapted += (
            "\nPlease organize your response with clear headings and numbered or "
            "bulleted lists where appropriate. Be thorough and precise."
        )

        return adapted

    def _adapt_gemini(self, prompt: str) -> str:
        """
        Gemini adapter.

        Preferences:
        - Concise, direct language
        - Bold markdown headers (**Section:**)
        - Bullet points over verbose prose
        - Minimal framing overhead
        """
        sections = self._parse_sections(prompt)

        task_raw = sections.get("Task", prompt)
        context = sections.get("Context", "")
        constraints = sections.get("Constraints", "")
        output_format = sections.get("Output Format", "")

        # Strip verbose framing lines from the task block
        task_clean = self._strip_verbose_framing(task_raw)

        adapted = f"**Task:**\n{task_clean.strip()}\n"

        if context:
            adapted += f"\n**Context:**\n{context.strip()}\n"

        if constraints:
            # Convert constraints to tight bullet points
            constraint_bullets = self._ensure_bullets(constraints)
            adapted += f"\n**Constraints:**\n{constraint_bullets}\n"

        if output_format:
            format_bullets = self._ensure_bullets(output_format)
            adapted += f"\n**Output Format:**\n{format_bullets}\n"

        return adapted

    def _adapt_deepseek(self, prompt: str) -> str:
        """
        DeepSeek adapter.

        Preferences:
        - Technical precision and explicit accuracy requirement
        - Markdown code block hints for technical content
        - Structured but compact format
        - Emphasis on correctness over brevity
        """
        sections = self._parse_sections(prompt)

        role = sections.get("Role", "a highly accurate technical assistant")
        task_raw = sections.get("Task", prompt)
        context = sections.get("Context", "")
        constraints = sections.get("Constraints", "")
        output_format = sections.get("Output Format", "")

        adapted = (
            "Provide technically accurate information. "
            f"You are acting as {role}.\n\n"
        )

        adapted += f"### Task\n{task_raw.strip()}\n"

        if context:
            adapted += f"\n### Context\n{context.strip()}\n"

        if constraints:
            adapted += f"\n### Constraints\n{constraints.strip()}\n"

        if output_format:
            adapted += f"\n### Output Format\n{output_format.strip()}\n"

        adapted += (
            "\n### Notes\n"
            "- Use markdown formatting throughout your response.\n"
            "- Wrap any code samples in appropriate ` ``` ` code blocks with language tags.\n"
            "- Prioritise correctness; flag any assumptions or uncertainties explicitly.\n"
            "- Include edge cases and error handling where relevant."
        )

        return adapted

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------

    def _parse_sections(self, prompt: str) -> dict[str, str]:
        """
        Parse a structured prompt produced by AMPOAEngine into named sections.

        Expects markdown-style headers: ``## Section Name``
        """
        sections: dict[str, str] = {}
        current_section: str | None = None
        buffer: list[str] = []

        for line in prompt.splitlines():
            header_match = re.match(r"^##\s+(.+)$", line)
            if header_match:
                if current_section is not None:
                    sections[current_section] = "\n".join(buffer).strip()
                current_section = header_match.group(1).strip()
                buffer = []
            else:
                if current_section is not None:
                    buffer.append(line)

        if current_section is not None:
            sections[current_section] = "\n".join(buffer).strip()

        return sections

    def _to_numbered_steps(self, text: str) -> str:
        """
        Convert a block of text into numbered steps.

        Lines that are already bullet points (- or *) become numbered items.
        Non-bullet paragraphs are kept as-is.
        """
        lines = text.splitlines()
        result_lines: list[str] = []
        counter = 1
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* "):
                result_lines.append(f"{counter}. {stripped[2:].strip()}")
                counter += 1
            else:
                result_lines.append(line)
        return "\n".join(result_lines)

    def _strip_verbose_framing(self, text: str) -> str:
        """
        Remove verbose framing sentences that add little value for Gemini.

        Targets patterns like "You are a … assistant." at the start of lines.
        """
        # Remove lines that start with "You are" (role framing)
        lines = text.splitlines()
        cleaned = [
            line for line in lines
            if not re.match(r"^\s*You are (an?|the|a)\s+", line, re.IGNORECASE)
        ]
        return "\n".join(cleaned).strip()

    def _ensure_bullets(self, text: str) -> str:
        """
        Ensure every non-empty line in *text* starts with a bullet (``-``).
        Lines already starting with ``-`` or ``*`` or digits are left alone.
        """
        lines = text.splitlines()
        result: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r"^[-*\d]", stripped):
                result.append(stripped)
            else:
                result.append(f"- {stripped}")
        return "\n".join(result)
