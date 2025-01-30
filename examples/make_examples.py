from pathlib import Path

import RATapi as RAT

examples = [
    "DSPC_custom_XY",
    "DSPC_custom_layers",
    "DSPC_standard_layers",
    "absorption",
    "domains_custom_XY",
    "domains_custom_layers",
    "domains_standard_layers",
]

for example in examples:
    p, _ = getattr(RAT.examples, example)()
    # TODO remove this when RascalSoftware/python-RAT/#126 is fixed
    # https://github.com/RascalSoftware/python-RAT/issues/126
    for custom_file in p.custom_files:
        custom_file.path = Path(".")
    example_folder = Path(f"./{example}/")
    example_folder.mkdir(parents=True, exist_ok=True)
    p.save(example_folder, "project")
    RAT.Controls().save(example_folder, "controls") 
