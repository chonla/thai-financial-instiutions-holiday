import json
import chevron
import os

print(os.getcwd())
print("Loading holidays...")
with open("data.json", "r") as c:
    data = json.load(c)

print("Writing holidays calendar...")
with open("CALENDAR.mustache", "r") as f:
    calendar_content = chevron.render(f, data)
    with open("CALENDAR.md", "w") as w:
        w.write(calendar_content)
