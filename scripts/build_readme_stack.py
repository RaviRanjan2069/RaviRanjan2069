"""Print the Tech Stack section (categories of icons with names) for README.md.

python scripts/build_readme_stack.py   then paste between the TECH-STACK markers.
"""

GROUPS = [
    ("Languages", [("java", "Java"), ("py", "Python"), ("js", "JavaScript")]),
    ("Frontend", [("html", "HTML"), ("css", "CSS"), ("js", "JavaScript")]),
    ("Backend & Database", [("spring", "Spring Boot"), ("fastapi", "FastAPI"), ("mongodb", "MongoDB"), ("mysql", "MySQL")]),
    ("DevOps & Tools", [("git", "Git"), ("github", "GitHub"), ("githubactions", "GitHub Actions"), ("docker", "Docker"), ("maven", "Maven"), ("vscode", "VS Code")]),
]

out = []
for title, items in GROUPS:
    out.append(f"<h4 align=\"center\">{title}</h4>")
    out.append("<table align=\"center\"><tr>")
    for icon, name in items:
        out.append(
            f'<td align="center" width="104"><img src="https://skillicons.dev/icons?i={icon}" width="48" height="48" alt="{name}" />'
            f"<br /><sub><b>{name}</b></sub></td>"
        )
    out.append("</tr></table>")
    out.append("")
print("\n".join(out))
