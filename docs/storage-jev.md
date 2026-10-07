# Jev for Skillry Storage

`storage` is a typed operation caller. It is not an agent client and receives no
`~/.storage/skills`, skill inventory, raw prompt hook or native agent identity.
The storage engine calls `skillry-jev operate --client storage` with a JSON
object on stdin. `skillry-jev status --client storage` reports local setup;
neither command reads a key into command arguments or output.

Set up the optional helper from a reviewed Skillry source or release with
`python3 tools/jev.py install --storage-only` first as a preview, then add
`--apply` when the operator chooses to install it. This updates the Jev runtime
and enables the `storage` operation identity. Existing Codex, Claude, Cursor
and Antigravity skill installations, hook chains and `config.json` secret
reference remain intact. A fresh storage-only helper is enabled for typed
public/synthetic operations; an existing helper retains its enabled setting.
No provider request occurs during setup. A fresh helper defaults to the local Keychain service
`skillry.typesafe` and the chosen account name. The menu can enroll a key with
Security.framework under the service/account shown by the storage engine; it
must never pass the key through argv or JSON configuration. A missing helper,
provider SDK or key is a truthful unavailable state, not permission to change
another client's credentials. The helper's provider Python environment must
have its declared TypeSafe SDK available before cloud operations can succeed.

The engine may send only shareable public or synthetic abstract technical
records, such as stable artifact class descriptors. It must not send private
paths, filenames, customer data, document text, transcripts or secrets. Example
stdin for a closed-set class proposal:

```json
{"operation":"classify","task":"Classify abstract storage artifacts","data_class":"synthetic","records":[{"id":"a","text":"A declared reproducible build output"}],"labels":{"reproducible":"Can be regenerated from protected source and lockfiles","durable":"A delivery requiring a verified archive receipt","review":"Insufficient context"}}
```

Consume only `status: "computed"`, `authority: "typed_data_only"`, and the
typed `result.buckets` and `result.review` fields. The local storage engine
still enforces roots, leases, source identity, hashes and receipts. On provider
failure, known deterministic classes continue; uncertain artifacts wait for
review. An AI result never grants deletion authority.
