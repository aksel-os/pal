# Pinned to latest unstable branch on 11.11.2025

let
  pkgs =
    import
      (fetchTarball "https://github.com/NixOS/nixpkgs/archive/f6b44b2401525650256b977063dbcf830f762369.tar.gz")
      { };

in
pkgs.mkShell {
  packages = with pkgs; [
    python312
    python312Packages.requests
    python312Packages.python-dotenv
  ];
}
