package api

// Options configures an App. Every field is listed in AppOptions and documented in docs/options.md;
// the team suite checks both.
type Options struct {
	// RequestLog logs every handled request on the toolkit's logger.
	RequestLog bool
	// MaxHeaderBytes rejects requests whose headers exceed it with 431.
	MaxHeaderBytes int
}

// AppOptions is the registry of Options fields.
var AppOptions = []string{"RequestLog", "MaxHeaderBytes"}

// RouteOptions configures one route. Every field is listed in RouteOptionNames and documented.
type RouteOptions struct {
	// Methods restricts the route to these methods; empty means all.
	Methods []string
}

// RouteOptionNames is the registry of RouteOptions fields.
var RouteOptionNames = []string{"Methods"}
