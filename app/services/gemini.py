from google import genai

from app.core.config import settings


if not settings.gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not configured")


client = genai.Client(
    api_key=settings.gemini_api_key
)

def generate_ai_response(
    prompt: str,
    previous_interaction_id: str | None = None
) -> tuple[str, str]:

    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt,
        previous_interaction_id=previous_interaction_id
    )

    return interaction.output_text, interaction.id


def stream_ai_response(
    prompt: str,
    previous_interaction_id: str | None = None
):
    stream = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt,
        previous_interaction_id=previous_interaction_id,
        stream=True
    )

    interaction_id = None

    for event in stream:

        if event.event_type == "step.delta" and event.delta:
            if (
                getattr(event.delta, "type", None) == "text"
                and getattr(event.delta, "text", None)
            ):
                yield ("text", event.delta.text)

        elif event.event_type == "interaction.completed":
            interaction_id = event.interaction.id

    yield ("completed", interaction_id)
