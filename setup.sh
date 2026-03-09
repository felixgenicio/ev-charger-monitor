#!/usr/bin/env bash
# Setup EV charger monitor: install deps and configure cron (every 5 min)
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create .env from example if missing
if [ ! -f "$DIR/.env" ]; then
  cp "$DIR/.env.example" "$DIR/.env"
  echo "Created .env — edit it and fill in CHARGER_1_ID and CHARGER_2_ID"
  exit 1
fi

# Create venv if needed
if [ ! -d "$DIR/.venv" ]; then
  python3 -m venv "$DIR/.venv"
fi
"$DIR/.venv/bin/pip" install -q -r "$DIR/requirements.txt"

# Run once to verify
"$DIR/.venv/bin/python" "$DIR/fetch_chargers.py"

# Add cron entry (idempotent)
CRON_CMD="*/5 * * * * $DIR/.venv/bin/python $DIR/fetch_chargers.py >> $DIR/data/fetch.log 2>&1"
( crontab -l 2>/dev/null | grep -v "fetch_chargers.py"; echo "$CRON_CMD" ) | crontab -

echo ""
echo "Done. Cron job registered:"
echo "  $CRON_CMD"
echo ""
echo "Serve the page with:"
echo "  cd $DIR && python3 -m http.server 8080"
echo "  Then open http://localhost:8080"
