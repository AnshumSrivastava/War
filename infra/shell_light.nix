{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz";
    sha256 = "03plivnr4cg0h8v7djf9g2jra09r45pmdiirmy4lvl2n1d4yb7ac";
  }) {
    config.allowUnfree = true;
  }
}:

let
  pythonWithPackages = pkgs.python312.withPackages (ps: with ps; [
    pyqt5
    # pyqtwebengine  <-- Omitted to bypass massive build/lock
    numpy
    pygame
    gymnasium
    supabase
    markdown
    flask
  ]);
in
pkgs.mkShell {
  buildInputs = [
    pythonWithPackages
    pkgs.xvfb-run
  ];

  shellHook = ''
    echo "LIGHT Development environment (No WebEngine)"
    export QTWEBENGINE_DISABLE_SANDBOX=1
    echo ""
    echo "To run the application (Headless):"
    echo "  xvfb-run python3 main.py"
  '';
}
