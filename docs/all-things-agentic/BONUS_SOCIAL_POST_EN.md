# Social post draft — do not publish automatically

Film production is a live constraint system: actor delays, daylight, location windows, dependencies, and missing coverage can invalidate a schedule in minutes.

I built **StudioGrid AI**, an AI Production Control Room for the Taskmaster track. Give it one bounded natural-language production goal. A tool-less Gemini 3.6 Flash router validates a typed intent, then a real Google ADK workflow on Vertex AI Agent Engine reasons over production state, calls private typed tools, and persists the result in Firestore.

The primary proof is fully autonomous: one command checks `SC_05`, finds missing `SH_12`/`SH_13`, and creates an `OPEN` alert with no follow-up click.

A second command creates an evidence-backed PENDING schedule proposal for Maya's 45-minute delay. The agent completes the operational work, but cannot approve its own consequential schedule change. Autonomy is not the same as authority.

Public demo: https://studiogrid-web-729921508335.europe-west3.run.app

#AllThingsAgenticHackathon #GoogleCloud #Gemini #GoogleADK

## Publication check

- Use X, LinkedIn, Instagram, or Facebook.
- Keep `#AllThingsAgenticHackathon` exactly as written.
- Attach only real deployed-product media.
- Publish only after the user explicitly approves the final wording and account.
