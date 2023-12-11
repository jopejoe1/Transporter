{
  description = "Dicord voice mover";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let

        pkgs = import nixpkgs { inherit system; };
      in rec {
        packages = flake-utils.lib.flattenTree {
          transporter = pkgs.stdenv.mkDerivation {
            pname = "transporter";
            version = "unstable-2023-12-11";

            src = ./.;

            propagatedBuildInputs = [
              (pkgs.python3.withPackages
                (python3Packages: with python3Packages; [ discordpy ]))
            ];
            dontUnpack = true;
            installPhase = "install -Dm755 ${./main.py} $out/bin/transporter";
          };
        };
        defaultPackage = packages.transporter;
        apps = {
          transporter = flake-utils.lib.mkApp {
            drv = packages.transporter;
            exePath = "/bin/transporter";
          };
        };
        defaultApp = apps.transporter;
      });
}
