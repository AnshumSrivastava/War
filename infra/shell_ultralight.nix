{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz";
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
    numpy
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
    echo "ULTRALIGHT Development environment (Bare Essentials)"
    export QTWEBENGINE_DISABLE_SANDBOX=1
    echo ""
    echo "To run the application:"
    echo "  python3 main.py"
  '';
}
