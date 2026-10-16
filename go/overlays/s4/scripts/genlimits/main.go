// Command genlimits writes api/limits_gen.go from config/limits/limits.json. Run it after editing the limits
// list: go run ./scripts/genlimits
package main

import (
	"encoding/json"
	"fmt"
	"go/format"
	"os"
	"sort"
)

const source = "config/limits/limits.json"
const target = "api/limits_gen.go"

func main() {
	raw, err := os.ReadFile(source)
	if err != nil {
		fmt.Fprintln(os.Stderr, "genlimits:", err)
		os.Exit(1)
	}
	var limits map[string]int
	if err := json.Unmarshal(raw, &limits); err != nil {
		fmt.Fprintln(os.Stderr, "genlimits:", err)
		os.Exit(1)
	}
	names := make([]string, 0, len(limits))
	for n := range limits {
		names = append(names, n)
	}
	sort.Strings(names)
	out := "// Code generated from " + source + " by scripts/genlimits. DO NOT EDIT.\n\npackage api\n\nvar limits = map[string]int{\n"
	for _, n := range names {
		out += fmt.Sprintf("\t%q: %d,\n", n, limits[n])
	}
	out += "}\n"
	formatted, err := format.Source([]byte(out))
	if err != nil {
		fmt.Fprintln(os.Stderr, "genlimits:", err)
		os.Exit(1)
	}
	if err := os.WriteFile(target, formatted, 0o644); err != nil {
		fmt.Fprintln(os.Stderr, "genlimits:", err)
		os.Exit(1)
	}
	fmt.Printf("wrote %s with %d limits\n", target, len(limits))
}
