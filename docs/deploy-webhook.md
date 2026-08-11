# Auto-deploy from GitHub (NixOS)

On push to `master`, GitHub hits a local webhook; the host `git pull`s. Static files only — no build, no nginx reload.

## One-time setup

1. **Deploy key** (read-only) on the host, added to the GitHub repo:

   ```bash
   sudo -u rbitcoin-site ssh-keygen -t ed25519 -N '' \
     -f /var/lib/rbitcoin-site/deploy_key -C rbitcoin.org-deploy
   # paste .pub into GitHub → Settings → Deploy keys (write access off)
   ```

2. **Clone** once:

   ```bash
   sudo -u rbitcoin-site env \
     GIT_SSH_COMMAND='ssh -i /var/lib/rbitcoin-site/deploy_key -o IdentitiesOnly=yes' \
     git clone --depth 1 git@github.com:reardencode/rbitcoin.org.git /var/www/rbitcoin.org
   ```

3. **Webhook secret** (not in the Nix store):

   ```bash
   sudo install -d -m 0750 /etc/rbitcoin-org
   echo "RBITCOIN_WEBHOOK_SECRET=$(openssl rand -hex 32)" | sudo tee /etc/rbitcoin-org/webhook.env
   sudo chmod 640 /etc/rbitcoin-org/webhook.env
   sudo chown root:rbitcoin-site /etc/rbitcoin-org/webhook.env
   # save the secret value for GitHub in the next step
   ```

4. **GitHub webhook**: Settings → Webhooks → Add  
   - URL: `https://rbitcoin.org/hooks/rbitcoin-org`  
   - Content type: `application/json`  
   - Secret: same as `RBITCOIN_WEBHOOK_SECRET`  
   - Events: **Just the push event**

5. Point nginx `root` at `/var/www/rbitcoin.org/public` (already). Apply the module below, then:

   ```bash
   sudo nixos-rebuild switch
   # smoke: push a commit, or:
   sudo -u rbitcoin-site /run/current-system/sw/bin/true  # ensure user exists
   sudo systemctl start rbitcoin-org-update.service
   journalctl -u webhook -u rbitcoin-org-update -n 40
   ```

## NixOS module

```nix
{ config, pkgs, lib, ... }:

let
  siteRoot = "/var/www/rbitcoin.org";
  key = "/var/lib/rbitcoin-site/deploy_key";
  repo = "git@github.com:reardencode/rbitcoin.org.git";

  update = pkgs.writeShellScript "rbitcoin-org-update" ''
    set -euo pipefail
    export PATH=${lib.makeBinPath [ pkgs.git pkgs.openssh pkgs.coreutils ]}
    export GIT_SSH_COMMAND="ssh -i ${key} -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes"
    cd ${siteRoot}
    git fetch --depth 1 origin master
    git merge --ff-only FETCH_HEAD
  '';
in
{
  users.users.rbitcoin-site = {
    isSystemUser = true;
    group = "rbitcoin-site";
    home = "/var/lib/rbitcoin-site";
    createHome = true;
  };
  users.groups.rbitcoin-site = {};

  systemd.tmpfiles.rules = [
    "d ${siteRoot} 0755 rbitcoin-site rbitcoin-site -"
    "d /var/lib/rbitcoin-site 0750 rbitcoin-site rbitcoin-site -"
  ];

  # Pull (webhook + backup timer both start this)
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

  # Webhook listens on loopback; nginx proxies HTTPS
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
                "parameter": { "source": "header", "name": "X-Hub-Signature-256" }
              }
            },
            {
              "match": {
                "type": "value",
                "value": "refs/heads/master",
                "parameter": { "source": "payload", "name": "ref" }
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
    # forceSSL / enableACME / root = "${siteRoot}/public" as you already have
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

Merge the `virtualHosts."rbitcoin.org"` block with your existing vhost (same `root`, TLS, etc.).

## Notes

- Secret stays in `/etc/rbitcoin-org/webhook.env` only (`hooksTemplated` + `getenv`).
- Webhook runs as `rbitcoin-site` and executes the same script as the timer — no polkit.
- `merge --ff-only` refuses non-fast-forward history.
- No build step; nginx keeps serving `public/`.
