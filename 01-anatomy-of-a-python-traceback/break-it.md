# Break It: Module 01

1. **Feed it a source line that looks like a frame.** A frame's source line is indented four
   spaces, and `FRAME_RE` allows leading whitespace, so a source line reading
   `File "x", line 1, in y` is taken for the next frame. Reproduce it. Then decide how to fix it
   (hint: real frames are indented exactly two spaces; source lines four).
2. **Add a log prefix:** put `2024-05-01 12:00:00 ERROR ` in front of the `Traceback` line. The
   parser skips ahead to the header, so this works. Now put a timestamp in front of *every*
   line. What breaks, and where would you strip the prefix (hint: before parsing, in one place)?
3. **Python 3.13 `add_note()`** prints extra lines after the exception line. Make them part of
   `message`, but stop at a blank line so a following log record is not swallowed.
