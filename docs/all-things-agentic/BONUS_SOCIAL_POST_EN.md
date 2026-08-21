# Social post draft — do not publish automatically

Film production is a live constraint system: actor delays, daylight, location windows, dependencies, and missing coverage can invalidate a schedule in minutes.

I built **StudioGrid AI**, an AI Production Control Room for the Taskmaster track. A real Google ADK multi-agent workflow on Vertex AI Agent Engine + Gemini 3.6 Flash turns a structured production event into a durable schedule proposal, using private typed tools and Firestore.

The agent performs the multi-step analysis and action. It can propose, but it cannot approve its own consequential schedule change. A production manager makes that decision, and the before/after state plus `HUMAN_DECISION` evidence persist across refresh.

The demo also includes a Coverage Agent that finds actual missing shots from planned/completed state.

Public demo: https://studiogrid-web-729921508335.europe-west3.run.app

#AllThingsAgenticHackathon #GoogleCloud #Gemini #GoogleADK

## Publication check

- Use X, LinkedIn, Instagram, or Facebook.
- Keep `#AllThingsAgenticHackathon` exactly as written.
- Attach only real deployed-product media.
- Publish only after the user explicitly approves the final wording and account.
