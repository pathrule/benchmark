# acme

The platform team's HTTP toolkit: an `App` with routes, options and middleware, a problem-format error
helper, generated platform limits and a small CLI. Standard library only.

```python
from acme import App, Request, Response

app = App(request_log=True)
app.route("/hello", lambda req: Response.text("hello"))
print(app.handle(Request("GET", "/hello")).body)
```

- Options: `docs/options.md`
- Errors: `docs/errors.md`
- Tests: `python3 -m unittest discover -s tests -t .`
- Team suite (platform CI): `python3 -m unittest discover -s teamtests -t .`
- Limits: edit `config/limits.json`, then `python3 scripts/gen_limits.py`
