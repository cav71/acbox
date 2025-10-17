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
        mapped = {  # type: ignore
            "event": {"repository": {}},
        }

        mapped["event"]["repository"]["name"] = data["event"]["repository"]["name"]
        mapped["ref"] = data["ref"]
        mapped["sha"] = data["sha"]
        mapped["run_number"] = data["run_number"]
        mapped["event"]["repository"]["default_branch"] = data["event"]["repository"]["default_branch"]
        mapped["ref_name"] = data["ref_name"]
        mapped["event"]["repository"]["html_url"] = data["event"]["repository"]["html_url"]

        path = here / f"github.{name}.json"
        print(f"writing {path}")
        path.write_text(json.dumps(mapped, indent=2))
