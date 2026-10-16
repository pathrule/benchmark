package api

import (
	"net/http"
	"testing"
)

func TestExactPathMatches(t *testing.T) {
	app := New(Options{})
	app.Route("/a", func(Request) Response { return Text(200, "a") })
	if got := app.Handle(Request{Method: "GET", Target: "/a"}); string(got.Body) != "a" {
		t.Fatalf("body %q", got.Body)
	}
}

func TestUnknownPathIs404(t *testing.T) {
	if got := New(Options{}).Handle(Request{Method: "GET", Target: "/nope"}); got.Status != 404 {
		t.Fatalf("status %d", got.Status)
	}
}

func TestMethodsOptionRestricts(t *testing.T) {
	app := New(Options{})
	app.Route("/p", func(Request) Response { return Text(200, "ok") }, RouteOptions{Methods: []string{"POST"}})
	if app.Handle(Request{Method: "GET", Target: "/p"}).Status != 404 || app.Handle(Request{Method: "POST", Target: "/p"}).Status != 200 {
		t.Fatal("methods option not applied")
	}
}

func TestMiddlewareWrapsHandler(t *testing.T) {
	app := New(Options{})
	app.Use(func(r Request, next Handler) Response { res := next(r); res.Set("X-Tagged", "yes"); return res })
	app.Route("/t", func(Request) Response { return Text(200, "t") })
	if got := app.Handle(Request{Method: "GET", Target: "/t"}); got.Get("X-Tagged") != "yes" {
		t.Fatalf("header %v", got.Header)
	}
}

func TestOversizedHeadersAnswer431(t *testing.T) {
	app := New(Options{MaxHeaderBytes: 10})
	if got := app.Handle(Request{Method: "GET", Target: "/", Header: http.Header{"X-Long": {"xxxxxxxxxxxxxxxxxxxx"}}}); got.Status != 431 {
		t.Fatalf("status %d", got.Status)
	}
}
