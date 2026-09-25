#!/usr/bin/env python3
"""Load the lab's explicit-context command script through vtysh.

Container adapter, not a production configuration transaction or rollback tool.
"""
import subprocess
import sys
from pathlib import Path

commands=[s.strip() for s in Path(sys.argv[1]).read_text().splitlines()
          if s.strip() and not s.strip().startswith('!')]
args=['vtysh']
for command in commands:
    args += ['-c',command]
result=subprocess.run(args,capture_output=True,text=True)
print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
errors=['authentication failure','processing failure','unknown command',
        'ambiguous command','% error','command incomplete']
raise SystemExit(result.returncode or int(any(e in (result.stdout+result.stderr).lower() for e in errors)))
