#!/usr/bin/env python
import json
from pathlib import Path

here = Path(__file__).parent


if __name__ == "__main__":
    mapper = {
        "beta": "beta.full.json",
        "main": "main.full.json",
        "tags": "tag.full.json",
    }
    for name, src in mapper.items():
        data = json.loads((here / src).read_text())
        mapped = dict(
            name=data["event"]["repository"]["name"],
            ref=data["ref"],
            sha=data["sha"],
            run_number=data["run_number"],
            default_branch=data["event"]["repository"]["default_branch"],
            ref_name=data["ref_name"],
            url=data["event"]["repository"]["html_url"],
        )
        path = here / f"github.{name}.json"
        print(f"writing {path}")
        path.write_text(json.dumps(mapped, indent=2))
