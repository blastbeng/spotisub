# Help

<div class="grid cards" markdown>

-   **Troubleshooting**
    ---
    Symptom → cause → fix, in the order these problems actually happen.

    [:octicons-arrow-right-24: Troubleshooting](troubleshooting.md)

-   **FAQ**
    ---
    What Spotisub is not, what it will not do, and the questions that come up before
    installing.

    [:octicons-arrow-right-24: FAQ](faq.md)

-   **Get help**
    ---
    Where to ask, and what to include so the question can be answered in one round.

    [:octicons-arrow-right-24: Community](community.md)

</div>

## The five-minute diagnosis

1. `curl -fsS http://127.0.0.1:5183/api/v1/utils/healthcheck` → must print `Ok!`.
2. **Check Subsonic** in the sidebar → proves credentials and path.
3. **System → Logs** → the last lines name the failing step.
4. If the dashboard is empty, the initial scan failed silently: see
   [Empty dashboard](troubleshooting.md#empty-dashboard).
5. If tracks are missing rather than everything failing, go to
   [Missing tracks](../guide/missing-tracks.md).
