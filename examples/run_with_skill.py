from pathlib import Path

from skillscope.instrumentation import AnthropicInstrumented, use_skill_from_path


def main() -> None:
    client = AnthropicInstrumented()
    skill_dir = Path(__file__).resolve().parent / "skills" / "brand-voice"
    with use_skill_from_path(
        skill_dir,
        files=["examples/skills/brand-voice/style-guide/brand-voice.md"],
        policy_required=False,
        progressive_level="referenced",
        model="claude-3-5-sonnet",
        operation="invoke_agent",
    ):
        response = client.messages_create(
            model="claude-3-5-sonnet",
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": "Rewrite this sentence in our brand voice: We are thrilled to announce a revolutionary feature.",
                }
            ],
        )
        print(response)


if __name__ == "__main__":
    main()
