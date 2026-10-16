package api

import (
	"log"
	"os"
)

// Logger is the toolkit's logger. Warnings about requests go here, never to stdout.
var Logger = log.New(os.Stderr, "acme: ", 0)
