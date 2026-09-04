# Evaluation Prompts

## Normal

Given a synthetic unary trace with `2S`, a proxy forwarding `1750m` after 250 ms, and completion after another 1,200 ms, produce the helper input and verify exact once-only deduction, monotonic propagation, and `ready` classification.

## Difficult edge

Given `1S`, Hop A forwarding `900m` after 100 ms, Hop B forwarding `900m` after another 200 ms, work active at 1,100 ms without cancellation, and a separate nine-digit timeout, separate grammar, expansion, and cancellation findings. Do not count parser failure as conformance.

## Should not activate

A REST client has a local five-second timeout, with no gRPC transport, `grpc-timeout`, propagation trace, or cancellation evidence. Explain why this workflow is `not_applicable` and do not manufacture a gRPC fixture.

## Assertions

- Normal: exact integer conversion; no findings; received/elapsed/available/sent values are explicit.
- Edge: grammar, Hop B expansion, and work-after-expiry findings are distinct; classification is `blocked`.
- Not applicable: no gRPC findings and no network action.
