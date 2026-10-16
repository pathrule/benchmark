package api

import (
	"io"
	"net/http"
)

// ServeHTTP adapts the App to net/http.
func (a *App) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	body, _ := io.ReadAll(r.Body)
	res := a.Handle(Request{Method: r.Method, Target: r.URL.RequestURI(), Header: r.Header, Body: body})
	for k, vs := range res.Header {
		for _, v := range vs {
			w.Header().Add(k, v)
		}
	}
	w.WriteHeader(res.Status)
	_, _ = w.Write(res.Body)
}
