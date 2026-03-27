{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz";
    sha256 = "03plivnr4cg0h8v7djf9g2jra09r45pmdiirmy4lvl2n1d4yb7ac";
  }) {
    config.allowUnfree = true;
    config.permittedInsecurePackages = [
      "qtwebengine-5.15.19"
    ];
  }
}:

let
  pythonWithPackages = pkgs.python312.withPackages (ps: with ps; [
    pyqt5
    pyqtwebengine
    numpy
    pygame
    gymnasium
    supabase
    markdown
    flask
    pytest
  ]);
in
pkgs.mkShell {
  buildInputs = [
    pythonWithPackages
    pkgs.xvfb-run
  ];

  shellHook = ''
    echo "Local development environment for Wargame Engine (Unstable)"
    export QTWEBENGINE_DISABLE_SANDBOX=1
    echo ""
    echo "To run the application (Headless):"
    echo "  xvfb-run python3 main.py"
    echo ""
    echo "To run the test suite:"
    echo "  python3 -m pytest test/ -v"
  '';
}
