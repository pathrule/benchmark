# Error responses

Errors the toolkit answers itself use the problem format (RFC 9457) through `problem()` in
`api/problem.ts`: `application/problem+json` with `type`, `title`, `status` and `detail`. Type URIs are
`https://errors.acme.dev/<slug>`; slugs are kebab-case nouns.

The default 404 and 431 are plain text for now.
