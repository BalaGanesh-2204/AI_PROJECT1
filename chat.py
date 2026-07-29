"""
chat.py

Groq-powered chat engine for the AI Expense Manager.

Responsibilities
- Stream assistant responses
- Handle tool calling
- Execute project tools
- Maintain conversation history
- Track turn-wise and running token usage
- Provide an interactive CLI loop

Compatible with the project structure:
- config.py
- tools.py
- store.py
- main.py

Author: Balaganesh
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from groq import Groq

from config import (
    MODEL_NAME,
    MAX_TOKENS,
    SYSTEM_PROMPT,
    TEMPERATURE,
    TOOLS,
    client,
    logger,
)
from tools import execute_tool, pretty_json


# ---------------------------------------------------------------------
# Terminal Colors
# ---------------------------------------------------------------------

class Term:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


def c(text: str, color: str) -> str:
    return f"{color}{text}{Term.RESET}"


# ---------------------------------------------------------------------
# Token Tracking
# ---------------------------------------------------------------------

@dataclass
class TokenStats:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(self, prompt: int = 0, completion: int = 0, total: int = 0) -> None:
        self.prompt_tokens += int(prompt or 0)
        self.completion_tokens += int(completion or 0)
        self.total_tokens += int(total or 0)

    def as_dict(self) -> Dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


def estimate_tokens_from_text(text: str) -> int:
    """
    Rough token estimation fallback.

    This is only used when the API does not return usage metadata.
    """
    if not text:
        return 0
    # Conservative approximation: 1 token ~= 4 characters in English text
    return max(1, len(text) // 4)


def estimate_tokens_from_messages(messages: List[Dict[str, Any]]) -> int:
    """
    Approximate token count from message payload.
    """
    total_chars = 0
    for msg in messages:
        total_chars += len(str(msg.get("role", "")))
        content = msg.get("content")
        if content:
            total_chars += len(str(content))
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            total_chars += len(json.dumps(tool_calls, ensure_ascii=False))
    return max(1, total_chars // 4)


# ---------------------------------------------------------------------
# Utility Helpers
# ---------------------------------------------------------------------

def safe_json_loads(data: str) -> Dict[str, Any]:
    """
    Parse JSON safely and return a dictionary.
    """
    if not data:
        return {}
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        # Try a small cleanup for malformed streamed JSON fragments
        cleaned = data.strip()
        cleaned = re.sub(r",\s*}", "}", cleaned)
        cleaned = re.sub(r",\s*]", "]", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Could not parse tool arguments JSON: {data}") from exc


def pretty_role(role: str) -> str:
    mapping = {
        "system": c("system", Term.DIM),
        "user": c("user", Term.CYAN),
        "assistant": c("assistant", Term.GREEN),
        "tool": c("tool", Term.YELLOW),
    }
    return mapping.get(role, role)


def print_banner() -> None:
    print(c("\n" + "=" * 72, Term.BLUE))
    print(c("AI EXPENSE MANAGER", Term.BOLD + Term.BLUE))
    print(c("Groq-powered CLI with tools + streaming", Term.DIM))
    print(c("=" * 72 + "\n", Term.BLUE))


def print_help() -> None:
    help_text = f"""
{c("Commands:", Term.BOLD)}
  {c("/help", Term.CYAN)}     Show this help
  {c("/exit", Term.CYAN)}     Exit the application
  {c("/quit", Term.CYAN)}     Exit the application
  {c("/clear", Term.CYAN)}    Clear the chat history
  {c("/history", Term.CYAN)}  Show message history count
  {c("/stats", Term.CYAN)}    Show token usage
  {c("/reset", Term.CYAN)}    Reset history and token stats

You can also ask things like:
  - Add an expense of 250 for food today
  - Show my expenses
  - What is my highest expense?
  - Delete expense 3
  - Give me a monthly summary
"""
    print(help_text.strip())


# ---------------------------------------------------------------------
# Chat Agent
# ---------------------------------------------------------------------

@dataclass
class ChatTurnResult:
    assistant_text: str = ""
    tool_calls_executed: int = 0
    usage: Dict[str, int] = field(default_factory=dict)
    raw_assistant_message: Dict[str, Any] = field(default_factory=dict)


class ExpenseChatAgent:
    """
    Groq chat agent for expense management.
    """

    def __init__(
        self,
        model: str = MODEL_NAME,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_TOKENS,
        max_tool_rounds: int = 8,
        history_limit: int = 40,
    ) -> None:
        self.client: Groq = client
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_tool_rounds = max_tool_rounds
        self.history_limit = history_limit

        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT.strip()}
        ]

        self.stats = TokenStats()
        self.turn_count = 0
        self.last_turn_usage: Dict[str, int] = {}

    # -----------------------------------------------------------------
    # Message History
    # -----------------------------------------------------------------

    def _trim_history(self) -> None:
        """
        Keep the history bounded so the conversation doesn't grow forever.
        """
        if len(self.messages) <= self.history_limit:
            return

        system_message = self.messages[0] if self.messages and self.messages[0]["role"] == "system" else None
        body = self.messages[1:] if system_message else self.messages[:]

        # Keep the most recent messages
        body = body[-(self.history_limit - 1):] if self.history_limit > 1 else []
        self.messages = [system_message] + body if system_message else body

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT.strip()}]
        self.stats = TokenStats()
        self.turn_count = 0
        self.last_turn_usage = {}

    def clear_conversation_only(self) -> None:
        """
        Clears user/assistant/tool messages but keeps the same session stats.
        """
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT.strip()}]

    def history_count(self) -> int:
        return max(0, len(self.messages) - 1)

    # -----------------------------------------------------------------
    # Usage Tracking
    # -----------------------------------------------------------------

    def _extract_usage_from_response(self, response: Any) -> Dict[str, int]:
        usage = getattr(response, "usage", None)
        if usage is None:
            return {}

        prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion = int(getattr(usage, "completion_tokens", 0) or 0)
        total = int(getattr(usage, "total_tokens", 0) or (prompt + completion))
        return {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": total,
        }

    def _record_usage(self, usage: Dict[str, int], fallback_messages: Optional[List[Dict[str, Any]]] = None, fallback_text: str = "") -> Dict[str, int]:
        """
        Record actual usage if available. Otherwise estimate usage.
        """
        if usage:
            self.stats.add(
                prompt=usage.get("prompt_tokens", 0),
                completion=usage.get("completion_tokens", 0),
                total=usage.get("total_tokens", 0),
            )
            return usage

        # Fallback estimation
        prompt_est = estimate_tokens_from_messages(fallback_messages or self.messages)
        completion_est = estimate_tokens_from_text(fallback_text)
        total_est = prompt_est + completion_est
        est = {
            "prompt_tokens": prompt_est,
            "completion_tokens": completion_est,
            "total_tokens": total_est,
            "estimated": 1,
        }
        self.stats.add(prompt=prompt_est, completion=completion_est, total=total_est)
        return est

    # -----------------------------------------------------------------
    # Streaming and Tool Handling
    # -----------------------------------------------------------------

    def _build_assistant_message_from_stream(
        self,
        stream: Any,
    ) -> ChatTurnResult:
        """
        Read a Groq stream and build the assistant message plus any tool calls.
        """
        text_parts: List[str] = []
        tool_call_map: Dict[int, Dict[str, Any]] = {}
        finish_reason: Optional[str] = None
        usage: Dict[str, int] = {}

        for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue

            choice = chunk.choices[0]
            delta = getattr(choice, "delta", None)

            if getattr(choice, "finish_reason", None):
                finish_reason = choice.finish_reason

            if delta is None:
                continue

            # Stream text
            content = getattr(delta, "content", None)
            if content:
                print(content, end="", flush=True)
                text_parts.append(content)

            # Stream tool calls
            tool_calls = getattr(delta, "tool_calls", None)
            if tool_calls:
                for tc in tool_calls:
                    idx = getattr(tc, "index", 0) or 0
                    item = tool_call_map.setdefault(
                        idx,
                        {
                            "id": getattr(tc, "id", None),
                            "type": "function",
                            "function": {
                                "name": None,
                                "arguments": "",
                            },
                        },
                    )

                    if getattr(tc, "id", None):
                        item["id"] = tc.id

                    fn = getattr(tc, "function", None)
                    if fn is not None:
                        fn_name = getattr(fn, "name", None)
                        fn_args = getattr(fn, "arguments", None)

                        if fn_name:
                            item["function"]["name"] = fn_name

                        if fn_args:
                            item["function"]["arguments"] += fn_args

            # Some Groq responses may expose usage in the stream tail
            if getattr(chunk, "usage", None):
                usage = self._extract_usage_from_response(chunk)

        assistant_text = "".join(text_parts).strip()
        tool_calls_list = [tool_call_map[i] for i in sorted(tool_call_map.keys()) if tool_call_map[i].get("function", {}).get("name")]

        assistant_message: Dict[str, Any] = {
            "role": "assistant",
            "content": assistant_text if assistant_text else None,
        }

        if tool_calls_list:
            assistant_message["tool_calls"] = tool_calls_list

        result = ChatTurnResult(
            assistant_text=assistant_text,
            tool_calls_executed=0,
            usage=usage,
            raw_assistant_message=assistant_message,
        )

        return result

    def _stream_completion(self, messages: List[Dict[str, Any]]) -> ChatTurnResult:
        """
        Create a Groq streamed completion and return the assembled message.
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        return self._build_assistant_message_from_stream(stream)

    def _non_stream_completion(self, messages: List[Dict[str, Any]]) -> ChatTurnResult:
        """
        Fallback completion when streaming fails.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=False,
        )

        choice = response.choices[0]
        message = choice.message

        assistant_message: Dict[str, Any] = {
            "role": "assistant",
            "content": getattr(message, "content", None),
        }

        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            cleaned_tool_calls: List[Dict[str, Any]] = []
            for tc in tool_calls:
                fn = getattr(tc, "function", None)
                cleaned_tool_calls.append(
                    {
                        "id": getattr(tc, "id", None),
                        "type": "function",
                        "function": {
                            "name": getattr(fn, "name", None) if fn else None,
                            "arguments": getattr(fn, "arguments", "") if fn else "",
                        },
                    }
                )
            assistant_message["tool_calls"] = cleaned_tool_calls

        return ChatTurnResult(
            assistant_text=getattr(message, "content", "") or "",
            tool_calls_executed=0,
            usage=self._extract_usage_from_response(response),
            raw_assistant_message=assistant_message,
        )

    def _call_model(self, messages: List[Dict[str, Any]]) -> ChatTurnResult:
        """
        Try streaming first, then fall back to non-streaming if needed.
        """
        try:
            return self._stream_completion(messages)
        except Exception as exc:
            logger.warning("Streaming failed, falling back to non-streaming: %s", exc)
            return self._non_stream_completion(messages)

    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single tool call and return a tool response message.
        """
        fn = tool_call.get("function", {})
        tool_name = fn.get("name")
        raw_args = fn.get("arguments", "") or ""

        if not tool_name:
            return {
                "role": "tool",
                "tool_call_id": tool_call.get("id"),
                "content": pretty_json({
                    "success": False,
                    "message": "Missing tool name in tool call.",
                }),
            }

        try:
            arguments = safe_json_loads(raw_args)
        except ValueError as exc:
            return {
                "role": "tool",
                "tool_call_id": tool_call.get("id"),
                "content": pretty_json({
                    "success": False,
                    "message": str(exc),
                }),
            }

        try:
            result = execute_tool(tool_name, arguments)
        except Exception as exc:
            logger.exception("Tool execution failed for %s", tool_name)
            result = {
                "success": False,
                "message": f"Tool execution failed: {exc}",
                "tool": tool_name,
            }

        return {
            "role": "tool",
            "tool_call_id": tool_call.get("id"),
            "content": pretty_json(result),
        }

    def _run_tool_rounds(self, assistant_message: Dict[str, Any]) -> int:
        """
        Execute tool calls from an assistant message until completion.
        """
        tool_calls = assistant_message.get("tool_calls") or []
        executed = 0

        if not tool_calls:
            return executed

        # First add the assistant message that contains the tool calls
        self.messages.append(assistant_message)

        for tool_call in tool_calls:
            tool_msg = self._execute_tool_call(tool_call)
            executed += 1
            self.messages.append(tool_msg)

            print(
                c("\n[tool result]", Term.YELLOW),
                tool_msg["content"],
                sep="\n",
            )

        self._trim_history()
        return executed

    # -----------------------------------------------------------------
    # Main Turn Handler
    # -----------------------------------------------------------------

    def chat_once(self, user_input: str) -> ChatTurnResult:
        """
        Process a single user message, handling tool calls if the model requests them.
        """
        self.turn_count += 1
        self.messages.append({"role": "user", "content": user_input})
        self._trim_history()

        start_time = time.time()
        total_tool_calls = 0
        last_result = ChatTurnResult()

        # Model/tool loop
        for round_index in range(self.max_tool_rounds):
            print(c("\nassistant> ", Term.GREEN), end="", flush=True)

            result = self._call_model(self.messages)
            last_result = result

            assistant_message = result.raw_assistant_message or {
                "role": "assistant",
                "content": result.assistant_text,
            }

            # If tool calls exist, execute them and continue the loop
            if assistant_message.get("tool_calls"):
                total_tool_calls += self._run_tool_rounds(assistant_message)
                continue

            # Final assistant content only
            self.messages.append(assistant_message)
            self._trim_history()
            break
        else:
            # Safety stop
            warning = {
                "role": "assistant",
                "content": "I reached the maximum tool-call depth for this turn.",
            }
            self.messages.append(warning)
            last_result.assistant_text = warning["content"]

        # Record token usage
        recorded_usage = self._record_usage(
            last_result.usage,
            fallback_messages=self.messages,
            fallback_text=last_result.assistant_text,
        )
        self.last_turn_usage = recorded_usage

        elapsed = time.time() - start_time

        # Pretty turn summary
        print()
        self._print_turn_summary(
            elapsed_seconds=elapsed,
            usage=recorded_usage,
            tool_calls=total_tool_calls,
        )

        return ChatTurnResult(
            assistant_text=last_result.assistant_text,
            tool_calls_executed=total_tool_calls,
            usage=recorded_usage,
            raw_assistant_message=last_result.raw_assistant_message,
        )

    # -----------------------------------------------------------------
    # Output Helpers
    # -----------------------------------------------------------------

    def _print_turn_summary(self, elapsed_seconds: float, usage: Dict[str, int], tool_calls: int) -> None:
        """
        Print token and timing summary after each turn.
        """
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        estimated = usage.get("estimated", 0)

        token_label = "estimated tokens" if estimated else "tokens"

        print(
            c(
                f"\n[turn {self.turn_count} summary] "
                f"prompt={prompt_tokens}, completion={completion_tokens}, "
                f"total={total_tokens}, tools={tool_calls}, "
                f"time={elapsed_seconds:.2f}s ({token_label})",
                Term.DIM,
            )
        )

        print(
            c(
                f"[running total] prompt={self.stats.prompt_tokens}, "
                f"completion={self.stats.completion_tokens}, "
                f"total={self.stats.total_tokens}",
                Term.DIM,
            )
        )

    def show_history_preview(self, max_items: int = 6) -> None:
        """
        Show a compact preview of the current conversation.
        """
        print(c("\nConversation history preview:", Term.BOLD))
        visible = self.messages[1:]  # Skip system prompt
        if not visible:
            print(c("  (empty)", Term.DIM))
            return

        for msg in visible[-max_items:]:
            role = pretty_role(msg.get("role", "?"))
            content = msg.get("content") or ""
            content = content.replace("\n", " ").strip()
            if len(content) > 100:
                content = content[:100] + "..."
            print(f"  {role}: {content}")

    def show_stats(self) -> None:
        """
        Show usage stats.
        """
        print(c("\nToken statistics:", Term.BOLD))
        print(f"  Prompt tokens    : {self.stats.prompt_tokens}")
        print(f"  Completion tokens: {self.stats.completion_tokens}")
        print(f"  Total tokens     : {self.stats.total_tokens}")
        print(f"  Turns completed  : {self.turn_count}")

        if self.last_turn_usage:
            print(c("\nLast turn:", Term.BOLD))
            for key, value in self.last_turn_usage.items():
                print(f"  {key}: {value}")

    # -----------------------------------------------------------------
    # Interactive CLI
    # -----------------------------------------------------------------

    def run_cli(self) -> None:
        """
        Start the interactive CLI session.
        """
        print_banner()
        print_help()

        while True:
            try:
                user_input = input(c("\nYou> ", Term.CYAN)).strip()

                if not user_input:
                    continue

                if user_input.lower() in {"/exit", "/quit"}:
                    print(c("Goodbye!", Term.MAGENTA))
                    break

                if user_input.lower() == "/help":
                    print_help()
                    continue

                if user_input.lower() == "/clear":
                    self.clear_conversation_only()
                    print(c("Conversation cleared.", Term.YELLOW))
                    continue

                if user_input.lower() == "/reset":
                    self.reset()
                    print(c("Conversation and token stats reset.", Term.YELLOW))
                    continue

                if user_input.lower() == "/history":
                    print(c(f"History messages: {self.history_count()}", Term.DIM))
                    self.show_history_preview()
                    continue

                if user_input.lower() == "/stats":
                    self.show_stats()
                    continue

                # Normal user query
                result = self.chat_once(user_input)

                if result.assistant_text:
                    print(result.assistant_text)

            except KeyboardInterrupt:
                print(c("\nInterrupted. Type /exit to quit.", Term.YELLOW))
                continue
            except EOFError:
                print(c("\nEOF received. Exiting.", Term.YELLOW))
                break
            except Exception as exc:
                logger.exception("Unexpected CLI error")
                print(c(f"\nError: {exc}", Term.RED))

    # -----------------------------------------------------------------
    # Non-interactive helper
    # -----------------------------------------------------------------

    def ask(self, user_input: str) -> str:
        """
        Programmatic single-turn helper.
        Returns the assistant text.
        """
        result = self.chat_once(user_input)
        return result.assistant_text


# ---------------------------------------------------------------------
# Standalone Execution
# ---------------------------------------------------------------------

def main() -> None:
    agent = ExpenseChatAgent()
    agent.run_cli()


if __name__ == "__main__":
    main()