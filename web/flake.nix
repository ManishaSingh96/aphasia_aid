{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts = {
      url = "github:hercules-ci/flake-parts";
      inputs.nixpkgs-lib.follows = "nixpkgs";
    };
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [];
      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
      perSystem = { config, pkgs, ... }:
        {
          devShells = {
            default = pkgs.mkShell {
              name = "app";
              buildInputs = [];
              nativeBuildInputs = [];
              packages = [
                # node
                pkgs.nodejs_20
                pkgs.nodePackages.pnpm
                # pkgs.nodePackages_latest.prettier
              ];
              # shellHook = '''';
              # postShellHook = '''';
            };
          };
        };
  };
}
