{ python3Packages }:

python3Packages.buildPythonApplication {
  name = "conn-proj1";
  src = ./.;
  format = "other";
  nativeCheckInputs = with python3Packages; [ flake8 mypy ];

  checkPhase = ''
    runHook preCheck
    mypy --strict *.py
    flake8 *.py
    runHook postCheck
  '';

  installPhase = ''
    runHook preBuild
    install -Dm755 -t $out/bin/ *.py
    runHook postBuild
  '';
}
