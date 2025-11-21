import os
import sys
# ensure project root is in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.config.settings import get_settings
p = get_settings().APP_LOG_DIR
print('APP_LOG_DIR=>', p)
print('exists=>', os.path.exists(p))
if os.path.exists(p):
    files = [os.path.join(p, f) for f in os.listdir(p) if os.path.isfile(os.path.join(p, f))]
    if not files:
        print('No log files found in APP_LOG_DIR')
    else:
        latest = max(files, key=os.path.getmtime)
        print('Latest log file =>', latest)
        print('\n--- last 300 lines ---\n')
        try:
            with open(latest, 'r', encoding='utf-8', errors='replace') as fh:
                lines = fh.readlines()
                for line in lines[-300:]:
                    print(line.rstrip())
        except Exception as e:
            print('Error reading file:', e)
else:
    print('listdir => N/A')
