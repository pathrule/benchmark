// Package api is the platform team's HTTP toolkit: an App with routes, options and middleware.
// Standard library only.
package api

import (
	"encoding/json"
	"net/http"
	"net/url"
	"strings"
)

// Request is what a handler receives. Target is the path with its optional query string.
type Request struct {
	Method string
	Target string
	Header http.Header
	Body   []byte
}

// Path is the request's path without the query string.
func (r Request) Path() string {
	u, err := url.Parse(r.Target)
	if err != nil {
		return r.Target
	}
	return u.Path
}

// Query is the parsed query string.
func (r Request) Query() url.Values {
	u, err := url.Parse(r.Target)
	if err != nil {
		return url.Values{}
	}
	return u.Query()
}

// Get returns a request header, or "" when absent.
func (r Request) Get(name string) string {
	if r.Header == nil {
		return ""
	}
	return r.Header.Get(name)
}

// Response is what a handler returns.
type Response struct {
	Status int
	Body   []byte
	Header http.Header
}

// Text builds a plain-text response.
func Text(status int, text string) Response {
	return Response{Status: status, Body: []byte(text), Header: http.Header{"Content-Type": {"text/plain; charset=utf-8"}}}
}

// JSON builds an application/json response.
func JSON(status int, value any) Response {
	body, _ := json.Marshal(value)
	return Response{Status: status, Body: body, Header: http.Header{"Content-Type": {"application/json"}}}
}

// Get returns a response header, or "" when absent.
func (r Response) Get(name string) string {
	if r.Header == nil {
		return ""
	}
	return r.Header.Get(name)
}

// Set sets a response header, creating the map when needed.
func (r *Response) Set(name, value string) {
	if r.Header == nil {
		r.Header = http.Header{}
	}
	r.Header.Set(name, value)
}

func headerBytes(h http.Header) int {
	n := 0
	for k, vs := range h {
		n += len(k) + len(strings.Join(vs, ","))
	}
	return n
}
