# Break It: Module 03

1. **Drop the `... 2 more` handling** and watch the Java assertion fail. Now make it worse: a
   `Caused by:` that appears *before* any frame of the wrapper. What should `... N more` do when
   there is nothing to copy?
2. **Node `new Promise (<anonymous>)` and `Array.map (<anonymous>)`** have no `file:line:col`.
   They do not match `NODE_FRAME`. Are they frames? What `kind` would you give them (module 04)?
3. **Go's `created by main.main in goroutine 1`** line is followed by a file line like any other
   frame. Teach `parse_go` to keep it as a frame named `created by main.main`.
