# Break It: Module 06

1. **Make it vulnerable on purpose.** Replace `match()` + `read_lines()` with
   `open(frame.file)`. Run `main.py`: which assertion catches it first?
2. **Remove the `commonpath` check from `read_lines`** but keep the index. The traversal
   strings still pass (why?), but the symlink check fails. What does that tell you about needing
   both layers?
3. **Case-insensitive filesystems.** `Pricing.py` vs `pricing.py` on Windows and macOS. The
   index lower-cases names; what happens on Linux with two files that differ only by case?
