#!/bin/bash
# Topelt-klõpsa seda faili — see käivitab kohaliku veebiserveri ja avab analüüsi brauseris.
# CORS-probleem file:// avamisel on lahendatud.
cd "$(dirname "$0")"
PORT=8765
echo "Käivitan veebiserveri pordis $PORT..."
echo "Sulgemiseks vajuta Ctrl+C."
echo ""
( sleep 1 && open "http://localhost:$PORT/analysis.html" ) &
python3 -m http.server $PORT
