import os
import time
from dotenv import load_dotenv
from groq import Groq

# -------------------------------------------------
# Load API Key
# -------------------------------------------------
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=api_key)

# -------------------------------------------------
# Model
# -------------------------------------------------
MODEL = "llama-3.3-70b-versatile"
# MODEL = "openai/gpt-oss-20b"

# -------------------------------------------------
# Conversation
# -------------------------------------------------
messages = [
    {
        "role": "system",
        "content": "You are a helpful AI assistant."
    }
]

# -------------------------------------------------
# Running Totals
# -------------------------------------------------
total_prompt_tokens = 0
total_completion_tokens = 0
total_tokens = 0

turn = 1

print("=" * 70)
print("             GROQ TERMINAL CHAT")
print("=" * 70)
print("Commands")
print(" exit  -> Quit")
print(" clear -> Clear conversation")
print("=" * 70)

while True:

    user = input(f"\nYou [{turn}]: ").strip()

    if user.lower() in ("exit", "quit"):
        print("\nGoodbye!")
        break

    if user.lower() == "clear":
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant."
            }
        ]
        print("Conversation cleared.")
        continue

    messages.append(
        {
            "role": "user",
            "content": user
        }
    )

    print("\nAssistant: ", end="", flush=True)

    assistant_reply = ""
    usage = None

    start = time.perf_counter()

    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        stream=True,
    )

    for chunk in stream:

        if chunk.choices:

            delta = chunk.choices[0].delta.content

            if delta:
                assistant_reply += delta
                print(delta, end="", flush=True)

            # Final chunk
            if chunk.choices[0].finish_reason:

                if getattr(chunk, "x_groq", None):
                    usage = chunk.x_groq.usage

    elapsed = time.perf_counter() - start

    print("\n")

    messages.append(
        {
            "role": "assistant",
            "content": assistant_reply
        }
    )

    # -----------------------------
    # Token Usage
    # -----------------------------
    if usage:

        total_prompt_tokens += usage.prompt_tokens
        total_completion_tokens += usage.completion_tokens
        total_tokens += usage.total_tokens

        tps = (
            usage.completion_tokens / elapsed
            if elapsed > 0 else 0
        )

        print("=" * 70)
        print(f"Turn {turn} Statistics")
        print("=" * 70)

        print(f"Prompt Tokens      : {usage.prompt_tokens}")
        print(f"Completion Tokens  : {usage.completion_tokens}")
        print(f"Total Tokens       : {usage.total_tokens}")
        print(f"Latency            : {elapsed:.2f} sec")
        print(f"Tokens / Second    : {tps:.2f}")

        print("-" * 70)

        print("Running Totals")
        print(f"Prompt Tokens      : {total_prompt_tokens}")
        print(f"Completion Tokens  : {total_completion_tokens}")
        print(f"Total Tokens       : {total_tokens}")

        print("=" * 70)

    else:
        print("\nToken usage not returned by this model/API")

    turn += 1