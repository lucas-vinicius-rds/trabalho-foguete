# Execute no PowerShell: .\gerar-executavel.ps1
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath '.venv-build\Scripts\python.exe')) {
        py -m venv --without-pip .venv-build
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível criar o ambiente de compilação.' }
    }

    py -m pip --python .venv-build\Scripts\python.exe install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível instalar as dependências de compilação.' }

    & .\.venv-build\Scripts\python.exe -m unittest -v
    if ($LASTEXITCODE -ne 0) { throw 'Os testes do jogo falharam.' }

    & .\.venv-build\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed --name JogoDeFoguete --distpath dist --workpath build --specpath build main.py
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível gerar o executável.' }

    New-Item -ItemType Directory -Path 'entrega\codigo-fonte' -Force | Out-Null
    Copy-Item -LiteralPath 'dist\JogoDeFoguete.exe' -Destination 'entrega\JogoDeFoguete.exe' -Force
    $sourceFiles = @('main.py', 'rocket.py', 'physics.py', 'test_game.py', 'requirements.txt', 'requirements-build.txt', 'gerar-executavel.ps1', 'LEIA-ME-ENTREGA.txt', 'README.md', 'preview.png', 'preview-game-over.png', '.gitattributes', '.gitignore')
    foreach ($sourceFile in $sourceFiles) {
        Copy-Item -LiteralPath $sourceFile -Destination 'entrega\codigo-fonte' -Force
    }
    Copy-Item -LiteralPath 'LEIA-ME-ENTREGA.txt' -Destination 'entrega\LEIA-ME.txt' -Force
    Compress-Archive -LiteralPath 'entrega' -DestinationPath 'entrega-foguete.zip' -Force
    Write-Host 'Entrega pronta: entrega-foguete.zip (executável e código-fonte).'
}
finally {
    Pop-Location
}
