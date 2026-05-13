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

tmp_dir="$(mktemp -d)"
metadata_file="$tmp_dir/metadata.json"
shape_file="$tmp_dir/shape.json"
result_file="$tmp_dir/launch-result.json"

cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

case "$OCI_COMPARTMENT_ID" in
  ocid1.compartment.*|ocid1.tenancy.*) ;;
  *)
    echo "OCI_COMPARTMENT_ID should be a compartment OCID, or the tenancy OCID when using the root compartment." >&2
    exit 2
    ;;
esac

case "$OCI_SUBNET_ID" in
  ocid1.subnet.*) ;;
  *)
    echo "OCI_SUBNET_ID must be a subnet OCID that starts with ocid1.subnet." >&2
    echo "Do not use a VCN, VNIC, route table, or security list OCID here." >&2
    exit 2
    ;;
esac

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

case "$OCI_IMAGE_ID" in
  ocid1.image.*) ;;
  *)
    echo "OCI_IMAGE_ID must be an image OCID that starts with ocid1.image." >&2
    exit 2
    ;;
esac

echo "Preflight: checking image and subnet access..."
image_error="$tmp_dir/image-error.txt"
if ! image_name="$(
  oci "${OCI_GLOBAL_ARGS[@]}" compute image get \
    --image-id "$OCI_IMAGE_ID" \
    --query 'data."display-name"' \
    --raw-output 2>"$image_error"
)"; then
  echo "Cannot access OCI_IMAGE_ID=${OCI_IMAGE_ID}." >&2
  echo "Make sure the image belongs to OCI_REGION=${OCI_REGION:-default profile region} and your API user can read instance images." >&2
  cat "$image_error" >&2
  exit 2
fi
echo "Preflight image: ${image_name}"

subnet_error="$tmp_dir/subnet-error.txt"
if ! subnet_json="$(
  oci "${OCI_GLOBAL_ARGS[@]}" network subnet get \
    --subnet-id "$OCI_SUBNET_ID" \
    --output json 2>"$subnet_error"
)"; then
  echo "Cannot access OCI_SUBNET_ID=${OCI_SUBNET_ID}." >&2
  echo "Most likely causes: wrong subnet OCID, subnet is in another region, or API user lacks use/read access to the subnet/VCN." >&2
  cat "$subnet_error" >&2
  exit 2
fi

mapfile -t SUBNET_DETAILS < <(
  printf '%s\n' "$subnet_json" |
    python3 -c 'import json,sys; d=json.load(sys.stdin)["data"]; print(d.get("display-name") or ""); print(d.get("compartment-id") or ""); print(d.get("availability-domain") or "regional"); print(str(d.get("prohibit-public-ip-on-vnic")).lower())'
)
subnet_name="${SUBNET_DETAILS[0]:-}"
subnet_compartment="${SUBNET_DETAILS[1]:-}"
subnet_ad="${SUBNET_DETAILS[2]:-regional}"
subnet_prohibit_public_ip="${SUBNET_DETAILS[3]:-}"

echo "Preflight subnet: ${subnet_name:-unnamed} (${subnet_ad})"
echo "Preflight subnet compartment: ${subnet_compartment:-unknown}"

if [ "$subnet_prohibit_public_ip" = "true" ]; then
  echo "This subnet is private or prohibits public IPv4 assignment, but the script launches with --assign-public-ip true." >&2
  echo "Use a public subnet, or change the script to launch without a public IP and use a bastion/VPN." >&2
  exit 2
fi

if [ "$subnet_ad" != "regional" ] && [ -z "${OCI_ADS:-}" ]; then
  OCI_ADS="$subnet_ad"
  echo "Subnet is AD-specific; limiting launch attempts to ${OCI_ADS}."
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
    if printf '%s\n' "$output" | grep -q 'NotAuthorizedOrNotFound'; then
      echo "Hint: launch_instance NotAuthorizedOrNotFound usually means the subnet is not usable from this region/compartment, or the API user lacks launch/network/volume permissions." >&2
      echo "Check OCI_SUBNET_ID first, then IAM policies for instance-family, virtual-network-family, volume-family, and app-catalog-listing." >&2
    fi
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
