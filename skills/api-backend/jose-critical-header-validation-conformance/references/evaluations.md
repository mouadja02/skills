# Evaluation Prompts

Three realistic prompts for baseline-versus-skill comparison. Each has deterministic assertions
checked against the validator's machine-readable output.

## Normal

> Given the decoded JOSE protected header
> `{"alg":"ES256","kid":"k1","crit":["exp-verified"],"exp-verified":true}` and a recipient that
> understands `exp-verified`, validate the `crit` header. Return JSON with `classification`,
> `crit_entries`, and `violations`, and state whether the token must be accepted or rejected.

Assertions: `classification` is `ready`; `crit_entries` equals `["exp-verified"]`; `violations` is empty; the token is not rejected on `crit` grounds.

## Difficult edge

> Validate each of these decoded JOSE headers independently, then classify every one:
> A `{"alg":"RS256","crit":["alg"]}`;
> B `{"alg":"RS256","crit":["foo","foo"],"foo":true}`;
> C `{"alg":"RS256","crit":["foo"]}`;
> D `{"alg":"RS256","b64":false,"crit":[]}`.
> Identify the specific violation for each and whether it is `blocked`.

Assertions: A blocked for naming a standard JOSE header; B blocked for a duplicate; C blocked for a dangling name; D blocked for `b64:false` without `b64` in `crit`. No case is reported `ready`.

## Should not activate

> A JWT protected header is `{"alg":"HS256","typ":"JWT","kid":"abc"}` and the user asks only whether
> the signature is valid. State whether JOSE critical-header validation should activate and why.

Assertion: the workflow does not activate; there is no `crit` field, so `classification` is `not_applicable` and no `crit` findings are emitted.
