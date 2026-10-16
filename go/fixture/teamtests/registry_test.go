// Package teamtests is the platform team's suite. The platform CI prepares the environment before
// running it.
package teamtests

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"regexp"
	"testing"

	"acme.example/toolkit/api"
)

func TestMain(m *testing.M) {
	if os.Getenv("ACME_TEAM_SUITE") != "1" {
		panic("team environment not prepared")
	}
	os.Exit(m.Run())
}

func documented(t *testing.T) map[string]bool {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join("..", "docs", "options.md"))
	if err != nil {
		t.Fatal(err)
	}
	out := map[string]bool{}
	for _, m := range regexp.MustCompile("(?m)^\\| `([A-Za-z]+)` \\|").FindAllStringSubmatch(string(raw), -1) {
		out[m[1]] = true
	}
	return out
}

func fields(v any) []string {
	t := reflect.TypeOf(v)
	out := make([]string, 0, t.NumField())
	for i := 0; i < t.NumField(); i++ {
		out = append(out, t.Field(i).Name)
	}
	return out
}

func TestEveryAppOptionIsRegisteredAndDocumented(t *testing.T) {
	docs := documented(t)
	registered := map[string]bool{}
	for _, n := range api.AppOptions {
		registered[n] = true
	}
	for _, f := range fields(api.Options{}) {
		if !registered[f] {
			t.Errorf("Options.%s is not in AppOptions", f)
		}
		if !docs[f] {
			t.Errorf("Options.%s is not documented in docs/options.md", f)
		}
	}
}

func TestEveryRouteOptionIsRegisteredAndDocumented(t *testing.T) {
	docs := documented(t)
	registered := map[string]bool{}
	for _, n := range api.RouteOptionNames {
		registered[n] = true
	}
	for _, f := range fields(api.RouteOptions{}) {
		if !registered[f] {
			t.Errorf("RouteOptions.%s is not in RouteOptionNames", f)
		}
		if !docs[f] {
			t.Errorf("RouteOptions.%s is not documented in docs/options.md", f)
		}
	}
}

func TestLimitsMatchTheirSource(t *testing.T) {
	gen, err := os.ReadFile(filepath.Join("..", "scripts", "genlimits", "main.go"))
	if err != nil {
		t.Fatal(err)
	}
	m := regexp.MustCompile(`const source = "([^"]+)"`).FindStringSubmatch(string(gen))
	raw, err := os.ReadFile(filepath.Join("..", m[1]))
	if err != nil {
		t.Fatal(err)
	}
	var limits map[string]int
	if err := json.Unmarshal(raw, &limits); err != nil {
		t.Fatal(err)
	}
	for name, value := range limits {
		if api.Limit(name) != value {
			t.Errorf("limit %s: generated %d, source %d (run go run ./scripts/genlimits)", name, api.Limit(name), value)
		}
	}
}
