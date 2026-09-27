#!/usr/bin/env bash
# Fetch the open YOLO11 COCO weights (AGPL-3.0, Ultralytics) once, with internet.
set -euo pipefail
cd "$(dirname "$0")"
for m in yolo11s yolo11n; do
  [ -f "$m.pt" ] || curl -fsSL -o "$m.pt" "https://github.com/ultralytics/assets/releases/download/v8.3.0/$m.pt"
done
sha256sum -c <<SUMS
85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5  yolo11s.pt
0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1  yolo11n.pt
SUMS
