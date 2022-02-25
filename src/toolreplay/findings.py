"""Finding types shared across the analysis modules.

A Finding is a single audit result. Findings sort deterministically by
(index, kind) so report output is byte-identical for identical input.
