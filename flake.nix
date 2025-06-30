{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts = { url = "github:hercules-ci/flake-parts"; inputs.nixpkgs-lib.follows = "nixpkgs"; };
    process-compose-flake.url = "github:Platonic-Systems/process-compose-flake";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        # https://community.flake.parts/process-compose-flake
        inputs.process-compose-flake.flakeModule
      ];
      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
      perSystem = { config, pkgs, ... }:
        let
          pyPackages = pkgs.python312Packages;
        in
        {
          process-compose = {
            localpg = {
              settings.processes = {
                postgres-server = {
                  command = ''pg_ctl -o "-p $PGPORT -h $PGHOST" -D $PGDATA start'';
                  is_daemon = true;
                  shutdown = { command = "pg_ctl -D $PGDATA stop"; };
                };
              };
            };
          };
          devShells = {
            default = pkgs.mkShell {
              name = "env";
              buildInputs = [];
              nativeBuildInputs = [];
              packages = [
                (pkgs.postgresql_17.withPackages (p: [ p.pg_uuidv7 ]))
                pkgs.pgcli
                pkgs.goose
              ];
              shellHook = ''
                mkdir -p $PGDATA
                if [ -d $PGDATA ]; then
                  initdb -U postgres $PGDATA --auth=trust >/dev/null
                fi
              '';
            };
            ci = pkgs.mkShell {
              name = "ci";
              packages = [];
            };
          };
        };
    };
}
