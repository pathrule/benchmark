// Command acme is the toolkit's CLI. Errors are one plain-text line on stderr with exit code 2.
package main

import (
	"fmt"
	"os"
	"strconv"

	"acme.example/toolkit/api"
)

func fail(message string) int {
	fmt.Fprintf(os.Stderr, "acme: %s\n", message)
	return 2
}

func usage() int {
	fmt.Fprintln(os.Stderr, "usage: acme limits <name> | acme version")
	return 2
}

func cmdLimits(args []string) int {
	if len(args) != 1 {
		return usage()
	}
	fmt.Println(strconv.Itoa(api.Limit(args[0])))
	return 0
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(usage())
	}
	switch os.Args[1] {
	case "limits":
		os.Exit(cmdLimits(os.Args[2:]))
	case "version":
		fmt.Println("acme 0.4.0")
	default:
		os.Exit(fail("unknown command " + strconv.Quote(os.Args[1])))
	}
}
