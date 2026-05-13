# GitHub Actions OCI A1 Retry

This guide runs `deploy/oracle/try_create_a1.sh` from GitHub Actions every 5 minutes so your own computer can sleep or shut down.

The workflow does not bypass Oracle capacity limits. It only retries normal OCI instance creation with a small `VM.Standard.A1.Flex` shape and stops trying once an instance with the same display name exists.

## 1. What You Need

- This repository pushed to GitHub.
- OCI tenancy, user, compartment, subnet, and image OCIDs.
- An OCI API signing key for GitHub Actions.
- An SSH public key to place on the VM.

Do not commit private keys into the repository. Put them in GitHub Actions secrets only.

Official docs:

- [GitHub Actions scheduled workflows](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#onschedule)
- [GitHub Actions secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [OCI API signing keys](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm)
- [OCI CLI launch instance](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/compute/instance/launch.html)

## 2. Create an OCI API Key

In the OCI Console:

1. Click the profile icon in the top-right corner.
2. Open **My profile**.
3. Open **API keys**.
4. Click **Add API key**.
5. Choose **Generate API key pair** or paste your own public key.
6. Download the private key and copy the configuration preview.

The configuration preview contains values like this:

```ini
[DEFAULT]
user=ocid1.user.oc1..xxxx
fingerprint=aa:bb:cc:dd:...
tenancy=ocid1.tenancy.oc1..xxxx
region=ap-singapore-2
key_file=<path-to-private-key>
```

You will put these values into GitHub secrets in the next step.

## 3. Create an SSH Key for the VM

This SSH key is different from the OCI API key. The API key lets GitHub call OCI. The SSH key lets you log in to the VM after it is created.

Create one locally, in WSL, Git Bash, or Cloud Shell:

```bash
ssh-keygen -t rsa -b 4096 -f mahjong-winner-ssh -C "mahjong-winner"
```

This creates:

- `mahjong-winner-ssh`: private SSH key. Keep this on your computer.
- `mahjong-winner-ssh.pub`: public SSH key. Put this in GitHub secret `OCI_SSH_PUBLIC_KEY`.

## 4. Add GitHub Secrets

Open your GitHub repository:

**Settings > Secrets and variables > Actions > New repository secret**

Add these secrets:

| Secret | Value |
| --- | --- |
| `OCI_USER_OCID` | `user` from the OCI config preview |
| `OCI_TENANCY_OCID` | `tenancy` from the OCI config preview |
| `OCI_FINGERPRINT` | `fingerprint` from the OCI config preview |
| `OCI_PRIVATE_KEY` | Full OCI API private key text, including `BEGIN PRIVATE KEY` and `END PRIVATE KEY` |
| `OCI_REGION` | For your screenshot: `ap-singapore-2` |
| `OCI_COMPARTMENT_ID` | Compartment OCID. Root compartment usually uses the tenancy OCID |
| `OCI_SUBNET_ID` | Public subnet OCID |
| `OCI_SSH_PUBLIC_KEY` | Full contents of `mahjong-winner-ssh.pub` |

Optional secrets:

| Secret | Value |
| --- | --- |
| `OCI_IMAGE_ID` | Optional. Use only if you want one exact Ubuntu image build |
| `OCI_ADS` | Comma-separated availability domain names if you want to force specific ADs |
| `OCI_INSTANCE_NAME` | Default is `mahjong-winner-a1` |

## 5. Add the Workflow

Create this file in your repository:

```text
.github/workflows/oci-script.yml
```

Paste this content:

```yaml
name: Try Create OCI A1 VM

on:
  workflow_dispatch:
  schedule:
    - cron: "*/5 * * * *"

concurrency:
  group: oci-script
  cancel-in-progress: false

permissions:
  contents: read
  actions: write

jobs:
  try-create:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    env:
      INSTANCE_NAME: ${{ secrets.OCI_INSTANCE_NAME || 'mahjong-winner-a1' }}
      OCI_USER_OCID: ${{ secrets.OCI_USER_OCID }}
      OCI_TENANCY_OCID: ${{ secrets.OCI_TENANCY_OCID }}
      OCI_FINGERPRINT: ${{ secrets.OCI_FINGERPRINT }}
      OCI_PRIVATE_KEY: ${{ secrets.OCI_PRIVATE_KEY }}
      OCI_REGION: ${{ secrets.OCI_REGION }}
      OCI_COMPARTMENT_ID: ${{ secrets.OCI_COMPARTMENT_ID }}
      OCI_SUBNET_ID: ${{ secrets.OCI_SUBNET_ID }}
      OCI_IMAGE_ID: ${{ secrets.OCI_IMAGE_ID }}
      OCI_SSH_PUBLIC_KEY: ${{ secrets.OCI_SSH_PUBLIC_KEY }}
      OCI_ADS: ${{ secrets.OCI_ADS }}
      SSH_PUBLIC_KEY_FILE: ${{ github.workspace }}/oci-instance-ssh.pub
      OCPUS: "2"
      MEMORY_GB: "8"
      BOOT_VOLUME_GB: "100"
      MAX_ATTEMPTS: "1"
      SLEEP_SECONDS: "0"

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install OCI CLI
        run: |
          python3 -m pip install --user oci-cli
          echo "$HOME/.local/bin" >> "$GITHUB_PATH"

      - name: Configure OCI CLI
        run: |
          mkdir -p "$HOME/.oci"

          cat > "$HOME/.oci/config" <<EOF
          [DEFAULT]
          user=${OCI_USER_OCID}
          fingerprint=${OCI_FINGERPRINT}
          tenancy=${OCI_TENANCY_OCID}
          region=${OCI_REGION}
          key_file=${HOME}/.oci/oci_api_key.pem
          EOF

          printf '%s\n' "$OCI_PRIVATE_KEY" > "$HOME/.oci/oci_api_key.pem"
          chmod 600 "$HOME/.oci/oci_api_key.pem"

          printf '%s\n' "$OCI_SSH_PUBLIC_KEY" > "$SSH_PUBLIC_KEY_FILE"

      - name: Skip if instance already exists
        id: existing
        run: |
          existing_id="$(
            oci compute instance list \
              --compartment-id "$OCI_COMPARTMENT_ID" \
              --display-name "$INSTANCE_NAME" \
              --all \
              --output json |
              python3 -c 'import json,sys; data=json.load(sys.stdin)["data"]; active=[i for i in data if i.get("lifecycle-state") not in ("TERMINATED","TERMINATING")]; print(active[0]["id"] if active else "")'
          )"

          if [ -n "$existing_id" ]; then
            echo "exists=true" >> "$GITHUB_OUTPUT"
            echo "Instance already exists: $existing_id"
          else
            echo "exists=false" >> "$GITHUB_OUTPUT"
            echo "No active instance named $INSTANCE_NAME found."
          fi

      - name: Try to create A1 instance once
        if: steps.existing.outputs.exists != 'true'
        run: |
          chmod +x deploy/oracle/try_create_a1.sh
          ./deploy/oracle/try_create_a1.sh

      - name: Disable retry workflow after success
        if: success()
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh workflow disable oci-script.yml --repo "$GITHUB_REPOSITORY"
          echo "Disabled oci-script.yml because the OCI instance already exists or was created successfully."
```

Why `MAX_ATTEMPTS` is `1`: GitHub Actions already schedules a new run every 5 minutes, so each job should try once and exit. Do not keep a single Actions runner sleeping for hours.

## 6. Run It

Commit and push the workflow file to GitHub.

Then open:

**GitHub repo > Actions > Try Create OCI A1 VM > Run workflow**

After that, the schedule will also run every 5 minutes until the VM is created.

## 7. After It Succeeds

When the workflow creates the VM, the Actions log prints:

```text
Created instance:
  instance_id: ...
  public_ip: ...
  ssh: ssh -i <private-key> ubuntu@...
```

The workflow disables itself after success with `gh workflow disable oci-script.yml`. If your repository or organization blocks `GITHUB_TOKEN` write access, disable it manually:

**GitHub repo > Actions > Try Create OCI A1 VM > ... > Disable workflow**

The skip step also prevents duplicate instances, so even a later rerun will not create a second VM with the same display name.

## 8. Troubleshooting

`Out of capacity`

This is expected. Let the scheduled workflow keep retrying.

`NotAuthenticated` or `401`

Check `OCI_USER_OCID`, `OCI_TENANCY_OCID`, `OCI_FINGERPRINT`, `OCI_PRIVATE_KEY`, and `OCI_REGION`. The private key must match the public API key uploaded to OCI.

`NotAuthorizedOrNotFound`

Usually means the API user does not have permission for the compartment, subnet, or image. If you are using a non-admin user, make sure its group can manage instances and use the VCN/subnet in that compartment.

`Invalid image` or `image not found`

The image OCID must be for the same region and must support `VM.Standard.A1.Flex`.

`Public IP was not assigned`

The subnet must be public and allow public IPv4 assignment. Fix the subnet/VCN setup before retrying.

`LimitExceeded`

Check that you are still inside Always Free limits. A safe first try is `1 OCPU`, `6 GB RAM`, and `100 GB` boot volume.
