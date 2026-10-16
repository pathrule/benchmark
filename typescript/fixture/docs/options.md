# Options

## App options

Members of `Options` (`api/options.ts`), passed to `new App({...})`. Every member is registered in
`AppOptions` and listed here; the team suite checks both.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `requestLog` | boolean | `false` | Log every handled request on the toolkit's logger. |
| `maxHeaderBytes` | number | `8192` | Requests whose headers exceed this answer 431. |

## Route options

Members of `RouteOptions`, passed to `app.route(path, handler, options)`. Registered in `RouteOptionNames`.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `methods` | string[] | all | The methods the route accepts. |
