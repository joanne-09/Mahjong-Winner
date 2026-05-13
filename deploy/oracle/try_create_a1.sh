#!/usr/bin/env bash
set -u

# Politely retries OCI VM.Standard.A1.Flex creation when Oracle reports no capacity.
# Run this from OCI Cloud Shell or any machine with OCI CLI configured.

required_vars=(
  OCI_COMPARTMENT_ID
  OCI_SUBNET_ID
  SSH_PUBLIC_KEY_FILE
)

for var_name in "${required_vars[@]}"; do
  if [ -z "${!var_name:-}" ]; then
    echo "Missing required environment variable: ${var_name}" >&2
    exit 2
  fi
done

if ! command -v oci >/dev/null 2>&1; then
  echo "oci CLI is not installed or not in PATH." >&2
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required for JSON escaping/parsing." >&2
  exit 2
fi

if [ ! -f "$SSH_PUBLIC_KEY_FILE" ]; then
  echo "SSH public key file not found: $SSH_PUBLIC_KEY_FILE" >&2
  exit 2
fi

INSTANCE_NAME="${INSTANCE_NAME:-mahjong-winner-a1}"
SHAPE="${SHAPE:-VM.Standard.A1.Flex}"
OCPUS="${OCPUS:-1}"
MEMORY_GB="${MEMORY_GB:-6}"
BOOT_VOLUME_GB="${BOOT_VOLUME_GB:-100}"
SLEEP_SECONDS="${SLEEP_SECONDS:-300}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-288}"
SSH_USER="${SSH_USER:-ubuntu}"
IMAGE_OS="${IMAGE_OS:-Canonical Ubuntu}"
IMAGE_OS_VERSION="${IMAGE_OS_VERSION:-24.04}"

OCI_GLOBAL_ARGS=()
if [ -n "${OCI_PROFILE:-}" ]; then
  OCI_GLOBAL_ARGS+=(--profile "$OCI_PROFILE")
fi
if [ -n "${OCI_REGION:-}" ]; then
  OCI_GLOBAL_ARGS+=(--region "$OCI_REGION")
fi

if [ -z "${OCI_IMAGE_ID:-}" ]; then
  echo "OCI_IMAGE_ID is not set. Looking up newest ${IMAGE_OS} ${IMAGE_OS_VERSION} image for ${SHAPE}..."
  OCI_IMAGE_ID="$(
    oci "${OCI_GLOBAL_ARGS[@]}" compute image list \
      --compartment-id "$OCI_COMPARTMENT_ID" \
      --shape "$SHAPE" \
      --operating-system "$IMAGE_OS" \
      --operating-system-version "$IMAGE_OS_VERSION" \
      --sort-by TIMECREATED \
      --sort-order DESC \
      --all \
      --query 'data[0].id' \
      --raw-output
  )"

  if [ -z "$OCI_IMAGE_ID" ] || [ "$OCI_IMAGE_ID" = "null" ]; then
    echo "Could not find an image. Set OCI_IMAGE_ID manually or adjust IMAGE_OS/IMAGE_OS_VERSION." >&2
    exit 2
  fi

  echo "Using OCI_IMAGE_ID=${OCI_IMAGE_ID}"
fi

if [ -n "${OCI_ADS:-}" ]; then
  IFS=',' read -r -a AD_NAMES <<< "$OCI_ADS"
else
  mapfile -t AD_NAMES < <(
    oci "${OCI_GLOBAL_ARGS[@]}" iam availability-domain list \
      --compartment-id "$OCI_COMPARTMENT_ID" |
      python3 -c 'import json,sys; print("\n".join(ad["name"] for ad in json.load(sys.stdin)["data"]))'
  )
fi

if [ "${#AD_NAMES[@]}" -eq 0 ]; then
  echo "No availability domains found. Set OCI_ADS manually if needed." >&2
  exit 2
fi

tmp_dir="$(mktemp -d)"
metadata_file="$tmp_dir/metadata.json"
shape_file="$tmp_dir/shape.json"
result_file="$tmp_dir/launch-result.json"

cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

export SSH_PUBLIC_KEY_FILE
python3 - <<'PY' > "$metadata_file"
import json
import os
from pathlib import Path

key = Path(os.environ["SSH_PUBLIC_KEY_FILE"]).read_text(encoding="utf-8").strip()
print(json.dumps({"ssh_authorized_keys": key}))
PY

python3 - <<PY > "$shape_file"
import json

print(json.dumps({"ocpus": float("$OCPUS"), "memoryInGBs": float("$MEMORY_GB")}))
PY

attempt=0
while true; do
  attempt=$((attempt + 1))
  echo "Attempt ${attempt}/${MAX_ATTEMPTS} at $(date -Is)"

  for ad in "${AD_NAMES[@]}"; do
    ad="$(echo "$ad" | xargs)"
    [ -z "$ad" ] && continue

    echo "Trying ${SHAPE} in ${ad} with ${OCPUS} OCPU / ${MEMORY_GB} GB RAM..."

    output="$(
      oci "${OCI_GLOBAL_ARGS[@]}" compute instance launch \
        --availability-domain "$ad" \
        --compartment-id "$OCI_COMPARTMENT_ID" \
        --display-name "$INSTANCE_NAME" \
        --shape "$SHAPE" \
        --shape-config "file://$shape_file" \
        --image-id "$OCI_IMAGE_ID" \
        --subnet-id "$OCI_SUBNET_ID" \
        --assign-public-ip true \
        --boot-volume-size-in-gbs "$BOOT_VOLUME_GB" \
        --metadata "file://$metadata_file" \
        --wait-for-state RUNNING \
        --output json 2>&1
    )"
    exit_code=$?

    if [ "$exit_code" -eq 0 ]; then
      printf '%s\n' "$output" > "$result_file"
      instance_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["data"]["id"])' "$result_file")"
      public_ip="$(
        oci "${OCI_GLOBAL_ARGS[@]}" compute instance list-vnics \
          --instance-id "$instance_id" \
          --output json |
          python3 -c 'import json,sys; data=json.load(sys.stdin)["data"]; print(data[0].get("public-ip") or "")'
      )"

      echo "Created instance:"
      echo "  instance_id: $instance_id"
      echo "  public_ip:   ${public_ip:-not assigned yet}"
      echo "  ssh:         ssh -i <private-key> ${SSH_USER}@${public_ip:-PUBLIC_IP}"
      exit 0
    fi

    if printf '%s\n' "$output" | grep -Eiq 'out of capacity|capacity'; then
      echo "No capacity in ${ad}. Will retry later."
      continue
    fi

    echo "OCI returned a non-capacity error. Stopping so you can fix the config:"
    printf '%s\n' "$output" >&2
    exit "$exit_code"
  done

  if [ "$MAX_ATTEMPTS" -gt 0 ] && [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
    echo "Reached MAX_ATTEMPTS=${MAX_ATTEMPTS}; no instance was created."
    exit 1
  fi

  echo "Sleeping ${SLEEP_SECONDS}s before retrying..."
  sleep "$SLEEP_SECONDS"
done
