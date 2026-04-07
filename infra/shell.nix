{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz") {
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
    markdown
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
