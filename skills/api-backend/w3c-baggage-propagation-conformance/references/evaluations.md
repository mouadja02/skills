# Evaluation Prompts

## Normal

Two received `baggage` field lines contain `userId=alice` and `serverNode=DF%2028,isProduction=false`. Verify member count, decoding, and extract/inject preservation.

## Difficult edge

Audit 65 combined members totaling 8100 bytes, including `route=version%3Dv2;vendor = raw` and `bad=%ZZ`. Separate percent, property, member-count, byte-count, and whole-member-drop rules.

## Should not activate

Only `traceparent` exists and the task is span-sampling tuning. Redirect to trace-context and sampling work.