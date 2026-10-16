# acme

The platform team's HTTP toolkit: an `App` with routes, options and middleware (`api`), a
problem-format error helper, generated platform limits and a small CLI (`cmd/acme`). Standard
library only.

```go
app := api.New(api.Options{RequestLog: true})
app.Route("/hello", func(api.Request) api.Response { return api.Text(200, "hello") })
res := app.Handle(api.Request{Method: "GET", Target: "/hello"})
```

- Options: `docs/options.md`
- Errors: `docs/errors.md`
- Tests: `go test ./api/...`
- Team suite (platform CI): `go test ./teamtests`
- Limits: edit `config/limits.json`, then `go run ./scripts/genlimits`
