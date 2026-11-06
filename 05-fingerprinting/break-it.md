# Break It: Module 05

1. **Two different bugs, same function.** `compute` fails with `KeyError: 'qty'` on line 12 and
   with `KeyError: 'price'` on line 30. Under this fingerprint they are one bug. Is that right?
   Try `with_lines=True`. Which would you want when counting occurrences in a log?
2. **A hot-fix renames the function.** The fingerprint changes. Is that a feature or a bug?
3. **Add Go's message class:** blank digits and quoted strings in the first 120 characters of the
   root message, for `panic`/`fatal error` types only, and show `index out of range [5]` and
   `[9]` collide while `nil pointer dereference` does not.
