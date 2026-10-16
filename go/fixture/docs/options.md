# Options

## App options

Fields of `api.Options`, passed to `api.New(...)`. Every field is registered in `api.AppOptions`
(`api/options.go`) and listed here; the team suite checks both.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `RequestLog` | bool | `false` | Log every handled request on the toolkit's logger. |
| `MaxHeaderBytes` | int | `8192` | Requests whose headers exceed this answer 431. |

## Route options

Fields of `api.RouteOptions`, passed to `app.Route(path, handler, opts)`. Registered in `api.RouteOptionNames`.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `Methods` | []string | all | The methods the route accepts. |
