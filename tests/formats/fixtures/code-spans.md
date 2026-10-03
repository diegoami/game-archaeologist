# Code-span link fixture

`tools/check_links.py` must skip links inside code spans. This file keeps that behaviour exercised:
before the commonmark code-span fix, the double-backtick span below was not recognised, so its link
was reported as broken.

A run of N backticks opens a span that closes at the next run of exactly N backticks, so this span
contains the single backtick and the link, and both are ignored:
``literal ` [code](missing-code-span.md)``

A single-backtick code span is ignored too: `[code](missing-single.md)`

A backslash-escaped backtick opens no span, so the next backtick does; its broken link stays hidden.
If the escaped backtick wrongly opened a span, it would eat that next backtick and expose the link:
\` `[code](missing-exposed-if-escaped-opens.md)`

This link sits outside every code span, so it is still checked, and it resolves:
[checker](../check_examples.py)
