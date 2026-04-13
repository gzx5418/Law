param(
    [string]$Query = "docx"
)

$skillPath = Join-Path $env:USERPROFILE ".agents\skills\docx\SKILL.md"
if (Test-Path $skillPath) {
    Write-Output "INSTALLED"
    Write-Output $skillPath
    exit 0
}

Write-Output "NOT_INSTALLED"
Write-Output "Searching marketplace..."
npx skills find $Query

