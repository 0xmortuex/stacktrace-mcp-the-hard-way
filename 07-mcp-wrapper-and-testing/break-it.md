# Break It: Module 07

1. **Raise a plain `ValueError` inside `parse_trace`** instead of `ToolError`. Run `main.py`
   and read what the client receives. Why is that message useless to an agent?
2. **Add a `print("debug")` to `report()`.** What happens to the session, and why?
3. **Remove the size cap** and send 50 MB. Then keep the cap and send 999,999 characters of
   `File "` repeated: does the timing assertion still hold? What would a quadratic regex do?
