package api

import "fmt"

// Handler takes a Request and returns a Response.
type Handler func(Request) Response

// Middleware wraps the next step.
type Middleware func(Request, Handler) Response

// Route is a registered path with its handler and options.
type Route struct {
	Path    string
	Handler Handler
	Options RouteOptions
}

func (r Route) accepts(method string) bool {
	if len(r.Options.Methods) == 0 {
		return true
	}
	for _, m := range r.Options.Methods {
		if m == method {
			return true
		}
	}
	return false
}

// App holds routes, options and middleware.
type App struct {
	opts        Options
	routes      []Route
	middlewares []Middleware
}

// New builds an App from its options.
func New(opts Options) *App {
	if opts.MaxHeaderBytes == 0 {
		opts.MaxHeaderBytes = 8192
	}
	return &App{opts: opts}
}

// Route registers a handler for an exact path.
func (a *App) Route(path string, h Handler, opts ...RouteOptions) *Route {
	var o RouteOptions
	if len(opts) > 0 {
		o = opts[0]
	}
	a.routes = append(a.routes, Route{Path: path, Handler: h, Options: o})
	return &a.routes[len(a.routes)-1]
}

// Routes lists the registered routes.
func (a *App) Routes() []Route {
	return append([]Route(nil), a.routes...)
}

// Use adds a middleware; middlewares run in the order added, outermost first.
func (a *App) Use(m Middleware) {
	a.middlewares = append(a.middlewares, m)
}

func (a *App) match(req Request) *Route {
	for i := range a.routes {
		if a.routes[i].Path == req.Path() && a.routes[i].accepts(req.Method) {
			return &a.routes[i]
		}
	}
	return nil
}

// Handle runs a request through the pipeline.
func (a *App) Handle(req Request) Response {
	if headerBytes(req.Header) > a.opts.MaxHeaderBytes {
		return Text(431, "Request Header Fields Too Large")
	}
	route := a.match(req)
	if route == nil {
		return Text(404, "Not Found")
	}
	var next Handler = route.Handler
	for i := len(a.middlewares) - 1; i >= 0; i-- {
		m, following := a.middlewares[i], next
		next = func(r Request) Response { return m(r, following) }
	}
	res := next(req)
	if a.opts.RequestLog {
		Logger.Println(fmt.Sprintf("%s %s -> %d", req.Method, req.Path(), res.Status))
	}
	return res
}
