# Break It: Module 02

1. **Three-level chain with mixed separators** (cause, then context). Assert the `via` values by
   hand: which exception gets which label, and why does the label live on the *earlier-printed*
   one?
2. **Input that ends right after a separator line.** The next block is empty, so
   `parse_traceback("")` raises. Decide what the server should do (hint: report what was
   parsed, flag it PARTIAL, say why).
3. **Nested group:** wrap the `ValueError` child in another `ExceptionGroup`. Extend
   `parse_group` to recurse into `_kid_kids` and return a tree. How do you define "root causes"
   for a tree?
