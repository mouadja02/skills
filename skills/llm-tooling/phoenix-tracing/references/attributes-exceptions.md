# Error and Exception Tracking

This document covers how failures are recorded on spans so they surface as errors in Phoenix.

## Overview

Errors are **not** an OpenInference concept — they use the standard OpenTelemetry mechanism, which
has two independent halves. You need both:

1. **Span status** set to `ERROR` — this is what makes Phoenix flag and filter the span.
2. **An exception event** carrying the type, message, and stacktrace — this is the detail.

Recording the exception without setting the status leaves the span looking successful in the UI.

## Span Status

| Status code | Meaning                                                        |
| ----------- | -------------------------------------------------------------- |
| `UNSET`     | Default. No explicit judgement — treated as success.            |
| `OK`        | Explicitly successful. Rarely needed.                           |
| `ERROR`     | The operation failed. Phoenix surfaces and filters on this.     |

A status description string should accompany `ERROR` with a short summary of the failure.

## Exception Event Attributes

The exception is recorded as a span **event** named `exception`, with these attributes:

| Attribute             | Type    | Description                                                |
| --------------------- | ------- | ---------------------------------------------------------- |
| `exception.type`      | String  | Exception class name (e.g. `RateLimitError`)                |
| `exception.message`   | String  | The exception message                                      |
| `exception.stacktrace`| String  | Formatted stacktrace                                       |
| `exception.escaped`   | Boolean | Whether the exception propagated out of the span's scope    |

Most SDKs populate all four from a `record_exception` helper — you rarely set them by hand.

## Python

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

with tracer.start_as_current_span("llm_call") as span:
    span.set_attribute("openinference.span.kind", "LLM")
    try:
        response = client.messages.create(...)
        span.set_attribute("output.value", response.content[0].text)
    except Exception as exc:
        span.record_exception(exc)
        span.set_status(Status(StatusCode.ERROR, str(exc)))
        raise
```

`record_exception()` creates the event; `set_status()` is what marks the span failed. Re-raising
keeps application behavior unchanged — tracing should never swallow an error.

## TypeScript

```typescript
import { SpanStatusCode } from "@opentelemetry/api";

tracer.startActiveSpan("llm_call", async (span) => {
  span.setAttribute("openinference.span.kind", "LLM");
  try {
    const response = await client.messages.create({ /* ... */ });
    span.setAttribute("output.value", response.content[0].text);
  } catch (err) {
    span.recordException(err as Error);
    span.setStatus({ code: SpanStatusCode.ERROR, message: (err as Error).message });
    throw err;
  } finally {
    span.end();
  }
});
```

Note the `finally { span.end() }` — an un-ended span never reaches Phoenix at all, which is the
most common reason a failure appears to vanish.

## Partial Failures

An operation can fail after producing useful output — a truncated completion, a retrieval that
returned some documents. Record both:

```json
{
  "openinference.span.kind": "LLM",
  "output.value": "The capital of France is",
  "llm.token_count.completion": 6,
  "metadata": "{\"finish_reason\": \"max_tokens\"}"
}
```

Reserve `ERROR` status for operations that did not deliver their result. A truncated-but-returned
completion is usually better modeled as successful with a `finish_reason` in metadata than as an
error, so error rates stay meaningful.

## Retries

Give each attempt its own span, so a call that succeeded on the third try shows two `ERROR` spans
and one success rather than a single ambiguous span. Tag them with the attempt number:

```json
{
  "openinference.span.kind": "LLM",
  "metadata": "{\"attempt\": 2, \"retry_reason\": \"rate_limit\"}"
}
```

## Common Mistakes

| Mistake                                    | Consequence                                            |
| ------------------------------------------- | ------------------------------------------------------ |
| `record_exception()` without `set_status()` | Span shows as successful; error rates under-report      |
| Catching and not re-raising                 | Changes application behavior to satisfy tracing         |
| Span never ended in the error path          | Span is dropped entirely; the failure is invisible      |
| Stacktraces containing PII                  | Leaks into the UI — see the production references       |
| One span covering all retry attempts        | Cannot distinguish a flaky call from a hard failure     |

## See Also

- `fundamentals-required-attributes.md` — attributes still required on a failed span
- `attributes-metadata.md` — recording `attempt` and `retry_reason`
- `production-python.md` / `production-typescript.md` — masking sensitive data before export
