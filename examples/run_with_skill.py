from skillscope.instrumentation import AnthropicInstrumented, use_skill


def main() -> None:
    client = AnthropicInstrumented()
    with use_skill(
        name="Brand Voice Editor (Safe Demo)",
        version="1.0.0",
        files=["examples/skills/brand_voice/style-guide/brand-voice.md"],
        policy_required=False,
        progressive_level="referenced",
        model="claude-3-5-sonnet",
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

