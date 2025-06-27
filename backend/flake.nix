{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts = {
      url = "github:hercules-ci/flake-parts";
      inputs.nixpkgs-lib.follows = "nixpkgs";
    };
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs@{
    nixpkgs,
    uv2nix,
    pyproject-nix,
    pyproject-build-systems,
    flake-parts,
    ...
  }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [];
      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
      perSystem = { config, pkgs, ... }:
        let
          pyPackages = pkgs.python312Packages;

          # packaging related
          python = pkgs.python312;
          pyprojectOverrides = final: prev: {
            # eg. if you get build setup-tools issues, this is what you'd need to fix
            # nats-py = prev.nats-py.overrideAttrs(old: {
            #   buildInputs = (old.buildInputs or []) ++ final.resolveBuildSystem ( {setuptools = [];});
            # });
          };

          # uv2nix stuff
          uvworkspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
          uvlockoverlay = uvworkspace.mkPyprojectOverlay {sourcePreference = "wheel";};
          uvpythonSet = (
            pkgs.callPackage pyproject-nix.build.packages { inherit python; }
          ).overrideScope(nixpkgs.lib.composeManyExtensions [
            pyproject-build-systems.overlays.default # for build tools
            uvlockoverlay                            # locked dependencies
            pyprojectOverrides                       # custom overrides
          ]);
        in
        {
          packages = rec {
            backend = uvpythonSet.mkVirtualEnv "env" uvworkspace.deps.default;
            backend_docker = pkgs.dockerTools.buildLayeredImage {
              name = builtins.getEnv "IMAGE_NAME";
              tag = builtins.getEnv "IMAGE_TAG";
              contents = [
                  backend
                  pkgs.cacert
                  pkgs.bashInteractive
                  pkgs.coreutils
              ];
              config = {
                # NOTE: What ever you specify under pyproject:[project.scripts]
                #       ends up in /bin
                Cmd = [ "./bin/server" ];
                Env = [
                  "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
                  # https://github.com/NixOS/nix/issues/795
                ];
              };
            };
          };
          devShells = {
            default = pkgs.mkShell {
              name = "env";
              buildInputs = [
                pkgs.python312
                pkgs.uv
              ];
              nativeBuildInputs = [];
              packages = [
                # typecheck
                pyPackages.mypy

                # formatting
                pyPackages.black

                # linting
                pyPackages.ruff
                pyPackages.bandit
                pkgs.pyright

                # debugging
                pyPackages.pudb
                pyPackages.ptpython
                # pkgs.memray
              ];
              shellHook = ''
                 uv sync
                 source .venv/bin/activate
                 export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc]}"
              '';
              # postShellHook = '''';
            };
            ci = pkgs.mkShell {
              name = "ci";
              packages = [];
            };
          };
        };
    };
}
