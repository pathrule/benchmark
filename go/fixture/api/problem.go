package api

import (
	"encoding/json"
	"net/http"
)

// TypeBase is the prefix of every problem type URI.
const TypeBase = "https://errors.acme.dev/"

// Problem answers an error the toolkit itself produces, in the problem format (RFC 9457).
func Problem(status int, title, detail, slug string) Response {
	body, _ := json.Marshal(map[string]any{"type": TypeBase + slug, "title": title, "status": status, "detail": detail})
	return Response{Status: status, Body: body, Header: http.Header{"Content-Type": {"application/problem+json"}}}
}
