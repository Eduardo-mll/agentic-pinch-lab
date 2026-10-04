<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

- Keep the scientific workspace as a single dashboard route with visual separation between AI interpretation and deterministic engine outputs, because a judge must distinguish their provenance at a glance.
- Structure the single workspace as anchored long-scroll sections, because navigation should expose the full scientific cycle without fragmenting its provenance across pages.
- Keep the discovery API contract and response validation in `src/lib/discovery-api.ts`, because the dashboard must render only backend-provided experiment values as live calculations.
