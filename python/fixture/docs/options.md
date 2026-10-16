# Options

## App options

Passed to `App(...)`. Every option is registered in `acme/options.py` (`APP_OPTIONS`) and listed here;
the team suite checks both.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `request_log` | bool | `False` | Log every handled request at INFO on the `acme` logger. |
| `max_header_bytes` | int | `8192` | Requests whose headers exceed this answer 431. |

## Route options

Passed to `app.route(path, handler, ...)`. Registered in `ROUTE_OPTIONS`.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `methods` | list[str] | all | The methods the route accepts. |
