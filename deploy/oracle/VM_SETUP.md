# Oracle Cloud VM Setup

This guide covers registering an Oracle Cloud Free Tier account and enabling an Always Free VM for this project.

## 1. Register Oracle Cloud Free Tier

1. Go to [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) and choose **Start for free**.
2. Enter your country, name, email, and complete the email verification.
3. Choose your **home region** carefully. Always Free compute resources must be created in the home region of the tenancy.
4. Complete identity verification. Oracle may ask for a phone number and a credit card. Oracle's Free Tier documentation says the card is not charged unless you upgrade the account.
5. After sign-up, open the Oracle email and sign in to the OCI Console.

Useful official docs:

- [Sign Up for the Free Oracle Cloud Promotion](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/signingup_topic-Sign_Up_for_Free_Oracle_Cloud_Promotion.htm)
- [Oracle Cloud Infrastructure Free Tier](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm)

## 2. Check Always Free Limits

For this project, prefer **VM.Standard.A1.Flex** because the tiny AMD micro instance is too small for PyTorch and YOLO.

Always Free Ampere A1 total allowance:

- Up to 4 OCPUs
- Up to 24 GB memory
- 200 GB total block volume storage

Recommended first VM:

- Shape: `VM.Standard.A1.Flex`
- OCPU: `2`
- Memory: `8 GB`
- Boot volume: `80-100 GB`
- Image: Ubuntu 24.04 or Ubuntu 22.04

This leaves room for rebuilding Docker images and keeps you inside the Always Free allocation.

If OCI shows `Out of host capacity`, try another availability domain in the same region, lower the OCPU/memory size, or retry later. This is common for Always Free A1 capacity.

Official doc: [Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)

## 3. Optional: Retry A1 Creation from Cloud Shell

If A1 capacity is unavailable, you can let OCI Cloud Shell retry politely until capacity appears. This does not bypass Oracle limits; it only repeats the same create-instance request at a safe interval and stops immediately after success.

Open **Cloud Shell** in the OCI Console, upload or paste this repository's script, then set the required values:

```bash
cd ~/mahjong-winner
chmod +x deploy/oracle/try_create_a1.sh

export OCI_COMPARTMENT_ID="ocid1.compartment.oc1..xxxx"
export OCI_SUBNET_ID="ocid1.subnet.oc1..xxxx"
export SSH_PUBLIC_KEY_FILE="$HOME/.ssh/id_rsa.pub"
```

Where to find each value:

- `OCI_COMPARTMENT_ID`: copy the compartment OCID. If you are using the root compartment, this is usually the tenancy OCID.
- `OCI_SUBNET_ID`: open **Networking > Virtual cloud networks > Subnets > your public subnet**, then copy its OCID.
- `SSH_PUBLIC_KEY_FILE`: path to the public key you want placed on the VM.

`OCI_IMAGE_ID` is optional. If you leave it unset, the script auto-selects the newest `Canonical Ubuntu 24.04` image that supports `VM.Standard.A1.Flex` in your region.

To pin one exact Ubuntu image OCID from Cloud Shell:

```bash
export OCI_REGION="ap-singapore-2"
export OCI_IMAGE_ID="$(
  oci compute image list \
    --region "$OCI_REGION" \
    --compartment-id "$OCI_COMPARTMENT_ID" \
    --shape VM.Standard.A1.Flex \
    --operating-system "Canonical Ubuntu" \
    --operating-system-version "24.04" \
    --sort-by TIMECREATED \
    --sort-order DESC \
    --all \
    --query 'data[0].id' \
    --raw-output
)"
echo "$OCI_IMAGE_ID"
```

Then start the retry loop:

```bash
export INSTANCE_NAME="mahjong-winner-a1"
export OCPUS="1"
export MEMORY_GB="6"
export BOOT_VOLUME_GB="100"
export SLEEP_SECONDS="300"
export MAX_ATTEMPTS="288"

./deploy/oracle/try_create_a1.sh
```

Useful optional settings:

- `OCI_ADS="AD-1,AD-2,AD-3"` limits which availability domains are tried. Leave it empty to auto-detect.
- `OCI_REGION="ap-singapore-2"` forces Singapore West when your OCI CLI profile has another default.
- `SSH_USER="opc"` prints the right SSH command if you use Oracle Linux instead of Ubuntu.
- `MAX_ATTEMPTS="0"` retries forever. Prefer a finite number if you leave Cloud Shell unattended.

Official CLI docs: [oci compute instance launch](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/compute/instance/launch.html)

If you want the retry loop to keep running after your computer sleeps or shuts down, use GitHub Actions instead:

[GitHub Actions A1 Retry](./VM_SCRIPT.md)

## 4. Create the VM

1. In OCI Console, open **Compute > Instances**.
2. Click **Create instance**.
3. Name it, for example `mahjong-winner`.
4. Image: choose **Ubuntu**.
5. Shape: choose **Ampere**, then `VM.Standard.A1.Flex`.
6. Set OCPU and memory, for example `2 OCPU / 8 GB`.
7. Networking:
   - Use **Create new virtual cloud network** if you do not already have one.
   - Make sure the subnet is public.
   - Make sure **Assign public IPv4 address** is enabled.
8. SSH keys:
   - Easiest: choose **Generate a key pair for me**.
   - Download both private and public keys before creating the instance.
   - Keep the private key safe. You cannot download it again later.
9. Click **Create**.

When the instance status becomes **Running**, copy its public IP address.

Official tutorial: [Launching Your First Linux Instance](https://docs.oracle.com/en-us/iaas/Content/Compute/tutorials/first-linux-instance/overview.htm)

## 5. Open Network Ports

OCI networking has an external firewall layer. Docker and Nginx can be correct, but traffic will still fail until the VCN allows it.

Open **Networking > Virtual cloud networks > your VCN > Security Lists > Default Security List** and add ingress rules:

| Purpose | Source CIDR | Protocol | Destination Port |
| --- | --- | --- | --- |
| SSH | your public IP `/32` | TCP | `22` |
| HTTP | `0.0.0.0/0` | TCP | `80` |
| HTTPS | `0.0.0.0/0` | TCP | `443` |

Keep SSH limited to your own IP if possible. If your IP changes often, temporarily use `0.0.0.0/0` for SSH only while setting up, then narrow it again.

Official networking docs:

- [Security Lists](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securitylists.htm)
- [Security Rules](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm)

## 6. SSH into the VM

For Ubuntu images, the username is usually `ubuntu`. For Oracle Linux images, the username is usually `opc`.

From macOS/Linux/WSL:

```bash
chmod 400 /path/to/private-key.key
ssh -i /path/to/private-key.key ubuntu@YOUR_PUBLIC_IP
```

From Windows PowerShell:

```powershell
ssh -i C:\path\to\private-key.key ubuntu@YOUR_PUBLIC_IP
```

If you chose Oracle Linux instead of Ubuntu:

```bash
ssh -i /path/to/private-key.key opc@YOUR_PUBLIC_IP
```

Official doc: [Connecting to a Linux Instance](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/connect-to-linux-instance.htm)

## 7. Open the VM Firewall

Ubuntu usually has UFW disabled by default, but check it:

```bash
sudo ufw status
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

If you use Oracle Linux, use firewalld:

```bash
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 8. Deploy This Project

After SSH works, follow the project deployment guide:

[Project Oracle Deployment README](./README.md)

The short version is:

```bash
git clone <your-repo-url>
cd Mahjong-Winner
cp .env.example .env
docker compose up -d --build
```

Then open:

```text
http://YOUR_PUBLIC_IP
```

## 9. Optional: Add a Domain and HTTPS

For a quick free HTTPS path, put the VM behind Cloudflare:

1. Create a DNS `A` record pointing to the VM public IP.
2. Enable Cloudflare proxy.
3. Use Cloudflare SSL/TLS mode.

If you do not use Cloudflare, add Certbot or Caddy later. Keep the `/socket.io/` WebSocket proxy behavior from the Nginx config because the game room uses live updates.
