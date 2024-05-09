{ texliveSmall, pandoc, python3Packages }:

python3Packages.buildPythonApplication {
  name = "conn-proj2";
  src = ./.;
  format = "other";

  nativeBuildInputs = [ pandoc texliveSmall ];
  buildInputs = with python3Packages; [ matplotlib ];

  nativeCheckInputs = with python3Packages; [ flake8 mypy ];

  buildPhase = ''
    runHook preBuild
    pandoc report.md -o report.pdf
    ./ex1.py
    ./ex2.py
    runHook postBuild
  '';

  checkPhase = ''
    runHook preCheck
    mypy --strict .
    flake8 --ignore E501 .
    runHook postCheck
  '';

  installPhase = ''
    runHook preBuild
    install -Dm755 -t $out/bin/ *.py
    runHook postBuild
  '';
}
