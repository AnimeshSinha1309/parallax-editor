## Inline Completion Debounce – Worklog

- lowered trigger threshold from 18→8 chars; raised idle fallback to 2 s to guarantee completions after pauses.
- validated async DSPy path (Predict.acall, fulfiller invoke) returns cards; ruled out LM regression.
- instrumented feed handler to log completion text, cancellation events, non-list fulfiller payloads.
- stopped cancelling in-flight LM calls when typing; only idle timer cancels now.
- reset char_count only when completion renders; cancellations no longer delay next trigger.
- replaced cursor-mismatch guard with length drift check (accept if |Δlen| ≤ 6).
- idle fallback now fires even below threshold so pausing always yields a suggestion.
- outstanding: explore adaptive thresholds, smarter cancellation once drift > tolerance, better UI affordances.