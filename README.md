# HTTP Service
Asynchronous http client build uppon aiohttp client.
Should be used in web applications due to use of prometheus like metrics.

## Configuration
* `http_connection_limit` - Number of opened connections in the internal aiohtpp pool. Client will wait for foree connection object if limit is reached
* `http_request_timeout` - Number to wait for responce. `int` values - seconds, 'float' values - fraction of a second. In case of timeout `None` is returned. In case of timout internal monitoring counter is incremented.

## Loggin
* http client has it's own `log: Logger` object named `http_client`.
* `app_name` - prefix which will be used as metrics prefix name e.g. `app_name_http_excetptions`

## Metrics
The client uses `prometheus_client` module to collect metrics.
Next metrics are collected:
* `http_requests_failed` - count of failed requests. e.g. server returned non 200 status.
* `http_requests_timeout` - count of timedout requesta.
* `http_exceptions` - count of internal exceptions coused by the client. e.g. rclient threw OS exception.

## Serder
Http client uses orjson as default json serializer and deserializer
