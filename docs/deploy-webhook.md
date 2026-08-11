# Auto-deploy from GitHub (NixOS)

On push to `master`, GitHub POSTs to this host; a loopback webhook verifies the request and runs `git pull`. Static site — no build, no nginx reload.

The repo is **public**, so git uses plain HTTPS (no deploy key). The webhook endpoint is still locked down so only real GitHub deliveries run the update.

## Security model

| Layer | What it does |
|-------|----------------|
| **HMAC secret** | GitHub signs the body with a shared secret (`X-Hub-Signature-256`). The hook rejects anything that fails verification. |
| **Loopback only** | `webhook` binds `127.0.0.1`; the public path is TLS nginx → proxy. |
| **Branch filter** | Only `refs/heads/master` runs the update. |
| **Secret not in store** | Secret lives in `/etc/rbitcoin-org/webhook.env` (`EnvironmentFile` + `getenv`), not in Nix. |

That HMAC is what “only real GitHub” means in practice: an attacker needs the secret to forge a valid signature. Keep the secret long and private; rotate it in GitHub + the env file if it leaks.

## One-time setup

1. **Clone** (after the user exists from the module, or create user first):

   ```bash
   sudo -u rbitcoin-site git clone --depth 1 \
     https://github.com/reardencode/rbitcoin.org.git /var/www/rbitcoin.org
   ```

2. **Webhook secret** (not in the Nix store):

   ```bash
   sudo install -d -m 0750 /etc/rbitcoin-org
   echo "RBITCOIN_WEBHOOK_SECRET=$(openssl rand -hex 32)" | sudo tee /etc/rbitcoin-org/webhook.env
   sudo chmod 640 /etc/rbitcoin-org/webhook.env
   sudo chown root:rbitcoin-site /etc/rbitcoin-org/webhook.env
   # keep a copy of the secret for the GitHub UI
   ```

3. **GitHub** → repo **Settings → Webhooks → Add webhook**

   | Field | Value |
   |-------|--------|
   | Payload URL | `https://rbitcoin.org/hooks/rbitcoin-org` |
   | Content type | `application/json` |
   | Secret | same as `RBITCOIN_WEBHOOK_SECRET` |
   | Events | **Just the push event** |
   | Active | on |

4. Apply the module (`nixos-rebuild switch`). Nginx `root` = `/var/www/rbitcoin.org/public`.

5. Smoke test:

   ```bash
   sudo systemctl start rbitcoin-org-update.service
   journalctl -u webhook -u rbitcoin-org-update -n 40
   # then push a commit; Recent Deliveries on GitHub should be green
   ```

## NixOS module

```nix
{ config, pkgs, lib, ... }:

let
  siteRoot = "/var/www/rbitcoin.org";
  repo = "https://github.com/reardencode/rbitcoin.org.git";

  update = pkgs.writeShellScript "rbitcoin-org-update" ''
    set -euo pipefail
    export PATH=${lib.makeBinPath [ pkgs.git pkgs.coreutils ]}
    cd ${siteRoot}
    if [ ! -d .git ]; then
      git clone --depth 1 ${lib.escapeShellArg repo} .
    fi
    git fetch --depth 1 origin master
    git merge --ff-only FETCH_HEAD
  '';
in
{
  users.users.rbitcoin-site = {
    isSystemUser = true;
    uid = 1002;
    group = "rbitcoin-site";
    home = "/home/rbitcoin-site";
    createHome = true;
  };
  users.groups.rbitcoin-site = {
    gid = 1002;
  };

  systemd.tmpfiles.rules = [
    "d ${siteRoot} 0755 rbitcoin-site rbitcoin-site -"
    "d /home/rbitcoin-site 0750 rbitcoin-site rbitcoin-site -"
  ];

  systemd.services.rbitcoin-org-update = {
    description = "Pull rbitcoin.org (ff-only)";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = {
      Type = "oneshot";
      User = "rbitcoin-site";
      Group = "rbitcoin-site";
      ExecStart = "${update}";
    };
  };

  services.webhook = {
    enable = true;
    ip = "127.0.0.1";
    port = 9000;
    urlPrefix = "hooks";
    openFirewall = false;
    user = "rbitcoin-site";
    group = "rbitcoin-site";
    hooksTemplated.rbitcoin-org = ''
      {
        "id": "rbitcoin-org",
        "execute-command": "${update}",
        "trigger-rule": {
          "and": [
            {
              "match": {
                "type": "payload-hmac-sha256",
                "secret": "{{ getenv "RBITCOIN_WEBHOOK_SECRET" }}",
                "parameter": {
                  "source": "header",
                  "name": "X-Hub-Signature-256"
                }
              }
            },
            {
              "match": {
                "type": "value",
                "value": "refs/heads/master",
                "parameter": {
                  "source": "payload",
                  "name": "ref"
                }
              }
            }
          ]
        }
      }
    '';
  };

  systemd.services.webhook.serviceConfig.EnvironmentFile = [
    "/etc/rbitcoin-org/webhook.env"
  ];

  services.nginx.virtualHosts."rbitcoin.org" = {
    # merge with existing: forceSSL, enableACME, root = "${siteRoot}/public"
    locations."/hooks/" = {
      proxyPass = "http://127.0.0.1:9000/hooks/";
      recommendedProxySettings = true;
    };
  };

  # Backup if a delivery is missed
  systemd.timers.rbitcoin-org-update = {
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "5min";
      OnUnitActiveSec = "30min";
      Persistent = true;
    };
  };
}
```

## Notes

- Public HTTPS clone/fetch — no SSH keys or tokens for git.
- Unsigned or wrong-secret POSTs to `/hooks/rbitcoin-org` do not run the update.
- `merge --ff-only` refuses non-fast-forward history.
- Webhook and timer both run the same script as `rbitcoin-site` (uid/gid **1002**, home **`/home/rbitcoin-site`**).
