# Module 03: Other Languages, Same Model

## The Concept

The model from module 01 does not change; only the parsers do. Three formats, three lessons.

## Java: `Caused by:` and `... 23 more`

```
java.lang.RuntimeException: failed to process order 42
	at com.acme.OrderService.process(OrderService.java:81)
	at com.acme.OrderController.post(OrderController.java:30)
	at com.acme.Main.main(Main.java:10)
Caused by: java.sql.SQLException: Connection refused
	at com.acme.Db.connect(Db.java:19)
	at com.acme.OrderService.process(OrderService.java:79)
	... 2 more
```

The JVM does not repeat frames that a cause shares with its wrapper. `... 2 more` means "my last
2 frames are the same as the enclosing exception's last 2". If you ignore it, the root cause
looks like it has two frames and the call path to `Main.main` is lost. The fix is to **copy**
those frames in from the enclosing exception, so each exception is complete on its own.

Also note: Java prints innermost first, and `java.base/java.lang.Thread.run` carries a module
prefix that must be stripped from the function name.

## Node: two frame shapes

```
TypeError: Cannot read properties of undefined (reading 'name')
    at getUserName (/srv/app/src/users.js:23:20)
    at /srv/app/src/routes.js:8:15
    at async main (/srv/app/src/index.js:4:3)
```

`at fn (file:line:col)` and the anonymous form `at file:line:col`. One regex handles both with an
optional `(?:(.+?) \()?` group. (The real server parses these by hand with `str.find`, because the
lazy group is quadratic on long adversarial lines. Module 07 tests that.)

## Go: pairs of lines

```
goroutine 1 [running]:
main.(*Server).handle(0xc000012345, {0x4d6a3a, 0x5})
	/app/server.go:42 +0x2c
```

A frame is **two lines**: the function with its argument list, then a tab, the file and line and
a `+0x2c` offset. The argument list is runtime noise (pointers!) and is removed by scanning from
the END of the line and matching parentheses, because the receiver `(*Server)` also has
parentheses.

## Detection

`detect()` looks for the strongest signal: a Python header, a `goroutine N [` line, Java frames
ending in `.java:12)`, Node frames ending in `:12:5)`. Order matters; Java's `(File.java:12)` must
be tried before Node's `(file:12:5)`.

## Run It

```
python main.py
```

## What You Learned

- A shared model makes N languages cost N small parsers, not N reports.
- Elision markers (`... N more`) carry information; expand them.
- Strip argument lists from the right, not with a regex.

Next: [Module 04: App vs Library Frames](../04-app-vs-library-frames/)
