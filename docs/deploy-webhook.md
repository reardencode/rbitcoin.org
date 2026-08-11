# Auto-deploy from GitHub (NixOS)

On push to `master`, GitHub POSTs to this host; a loopback webhook verifies the request and runs `git pull`. Static site — no build, no nginx reload.

The repo is **public**, so git uses plain HTTPS (no deploy key). The webhook endpoint is still locked down so only real GitHub deliveries run the update.

**On-disk layout (only these trees):**

| Path | Role |
|------|------|
| `/var/www/rbitcoin.org` | Git clone; nginx `root` → `…/public` |
| `/home/rbitcoin-site` | User home (uid/gid **1002**), update script, webhook secret |

No deploy files under `/etc` or elsewhere.

## Security model

| Layer | What it does |
|-------|----------------|
| **HMAC secret** | GitHub signs the body (`X-Hub-Signature-256`). Invalid signatures do not run the update. |
| **Loopback only** | `webhook` binds `127.0.0.1`; public path is TLS nginx → proxy. |
| **Branch filter** | Only `refs/heads/master` triggers the pull. |
| **Secret not in Nix store** | Secret file under the home dir only. |

Keep the secret long; rotate it in GitHub and the env file if it leaks.

## One-time setup

1. **User + dirs** (or let the module create the user, then):

   ```bash
   sudo install -d -m 0755 -o rbitcoin-site -g rbitcoin-site /var/www/rbitcoin.org
   sudo install -d -m 0750 -o rbitcoin-site -g rbitcoin-site /home/rbitcoin-site
   ```

2. **Clone:**

   ```bash
   sudo -u rbitcoin-site git clone --depth 1 \
     https://github.com/reardencode/rbitcoin.org.git /var/www/rbitcoin.org
   ```

3. **Webhook secret** (under home only):

   ```bash
   secret=$(openssl rand -hex 32)
   echo "RBITCOIN_WEBHOOK_SECRET=$secret" | sudo tee /home/rbitcoin-site/webhook.env
   sudo chown rbitcoin-site:rbitcoin-site /home/rbitcoin-site/webhook.env
   sudo chmod 600 /home/rbitcoin-site/webhook.env
   # save $secret for the GitHub UI
   ```

4. **GitHub** → **Settings → Webhooks → Add webhook**

   | Field | Value |
   |-------|--------|
   | Payload URL | `https://rbitcoin.org/hooks/rbitcoin-org` |
   | Content type | `application/json` |
   | Secret | same as `RBITCOIN_WEBHOOK_SECRET` |
   | Events | **Just the push event** |
   | Active | on |

5. Apply the module (`nixos-rebuild switch`). Nginx `root` = `/var/www/rbitcoin.org/public`.

6. Smoke test:

   ```bash
   sudo systemctl start rbitcoin-org-update.service
   journalctl -u webhook -u rbitcoin-org-update -n 40
   # push a commit; Recent Deliveries should be green
   ```

## NixOS module

```nix
{ config, pkgs, lib, ... }:

let
  siteRoot = "/var/www/rbitcoin.org";
  home = "/home/rbitcoin-site";
  repo = "https://github.com/reardencode/rbitcoin.org.git";
  updatePath = "${home}/update.sh";
  secretPath = "${home}/webhook.env";

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
    home = home;
    createHome = true;
  };
  users.groups.rbitcoin-site = {
    gid = 1002;
  };

  # Install update script into the home dir (not referenced from /etc)
  system.activationScripts.rbitcoin-site = lib.stringAfter [ "users" ] ''
    install -d -m 0755 -o rbitcoin-site -g rbitcoin-site ${siteRoot}
    install -d -m 0750 -o rbitcoin-site -g rbitcoin-site ${home}
    install -m 0755 -o rbitcoin-site -g rbitcoin-site ${update} ${updatePath}
  '';

  systemd.services.rbitcoin-org-update = {
    description = "Pull rbitcoin.org (ff-only)";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = {
      Type = "oneshot";
      User = "rbitcoin-site";
      Group = "rbitcoin-site";
      ExecStart = updatePath;
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
        "execute-command": "${updatePath}",
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

  systemd.services.webhook.serviceConfig.EnvironmentFile = [ secretPath ];

  services.nginx.virtualHosts."rbitcoin.org" = {
    # merge with existing: forceSSL, enableACME, root = "${siteRoot}/public"
    locations."/hooks/" = {
      proxyPass = "http://127.0.0.1:9000/hooks/";
      recommendedProxySettings = true;
    };
  };

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

- Runtime files: site under `/var/www/rbitcoin.org`; script + secret under `/home/rbitcoin-site`.
- Public HTTPS clone/fetch — no SSH keys or tokens for git.
- HMAC-invalid POSTs do not pull.
- `merge --ff-only` refuses non-fast-forward history.
- Webhook and timer both run `/home/rbitcoin-site/update.sh` as uid/gid **1002**.
