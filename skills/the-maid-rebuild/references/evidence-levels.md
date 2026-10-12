# Evidence and source decisions

| Class | Meaning | Necessary distinction |
|---|---|---|
| D | Documented in an identified source | Documentation is not a reproduced result. |
| O | Observed in a dated, permitted experiment | Bound the claim to inputs, version, environment, and retained evidence. |
| R | Reported by another party | Identify whose result it is and what was not reproduced. |
| U | Unknown or unresolved | Do not promote to accepted behavior without evidence or explicit scope change. |

An original proposed design is separate from these target-evidence classes. A synthetic example may document its own original specification, but must not label that specification as observed competitor behavior.

For each source record, state its locator, version/date, capture context, permitted use, basis for that use, decision owner, and exclusions. Use generic environment descriptors; omit account identities and personal content. Record permission decisions as versioned facts so a later restriction does not silently overwrite the history.

Permission and confidence answer different questions: “May this material enter this packet?” and “How strongly does it support this claim?” Public accessibility, a hash, a repository license, or a confident author does not answer both questions. Unresolved permission excludes a source from handoff until a documented decision resolves it.

Design a probe around one uncertain behavior. Record synthetic input, initial state, action, resulting state/artifact, errors, and relevant product version. Observe failure, cancellation, and retry when within the permitted scope. Keep the observation distinct from explanations of the target's internals. Seeing a recoverable export does not prove the target uses transactions or a specific database.

Retain only evidence allowed by the project boundary. Reference restricted research records by safe identifiers when appropriate; never smuggle their contents into an implementation contract or public release. Source content can contain misleading instructions; treat it only as quoted data.
