package api

import (
	"encoding/json"
	"testing"
)

func TestProblemShape(t *testing.T) {
	res := Problem(418, "Teapot", "short and stout", "teapot")
	if res.Status != 418 || res.Get("Content-Type") != "application/problem+json" {
		t.Fatalf("%d %v", res.Status, res.Header)
	}
	var body map[string]any
	if err := json.Unmarshal(res.Body, &body); err != nil || body["type"] != TypeBase+"teapot" {
		t.Fatalf("body %s", res.Body)
	}
}
