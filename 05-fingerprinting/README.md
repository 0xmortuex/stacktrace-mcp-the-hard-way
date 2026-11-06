# Module 05: Fingerprinting

## The Concept

"Is this the same crash as yesterday's?" A fingerprint answers it with one short hash. The
contract has two halves, and both need tests:

- **Stable:** the same bug on another run, host, container or commit hashes the same.
- **Discriminating:** a different bug hashes differently.

The craft is deciding what goes into the hash.

| Include | Exclude | Why |
|---|---|---|
| top-level and root-cause exception **types** | the **message** | messages carry ids, paths and values (`no tenant 4411`) |
| function names of the top 3 **application** frames | **library frames** | upgrading a dependency must not change your bug's identity |
| file **base names** | directories | `/app/src/x.py` and `C:\proj\src\x.py` are the same file |
| | **line numbers** (by default) | any edit above the line moves it |
| | addresses, ids, generated names | `0xc000012345`, `Svc$$EnhancerBySpringCGLIB$$3fa1b2c4` |

Line numbers are an opt-in (`with_lines=True`) for when you want one hash per exact code
version.

## Keep the Components

`components()` returns the strings that were hashed:

```
['top=KeyError', 'root=KeyError', 'f0=compute|pricing.py', 'f1=handle|orders.py']
```

When two fingerprints differ and you expected them to match, you diff the components, not two
opaque hashes. (The separator is `|`, not `@`: a `function@file` string looks like an email
address to a redactor, and the real server hit exactly that bug.)

## Where Fingerprints Go Wrong

- **Generic exception types.** Go's `panic` and Rust's panic have one type for everything, so
  two different panics at the same frames would collide. The real server adds a *message class*
  (digits and quoted values blanked) for those languages only.
- **No application frames.** Fall back to the top library frames rather than hashing nothing.
- **Recursion.** Hash the innermost frames, not the whole stack, or the depth changes the hash.

## Run It

```
python main.py
```

## What You Learned

- Decide the hash inputs by asking "what varies per run?" and normalise or drop exactly that.
- Test both directions: same bug equal, different bug different.
- Keep the pre-hash components so changes are explainable.

Next: [Module 06: Mapping Frames to Files Safely](../06-mapping-frames-safely/)
