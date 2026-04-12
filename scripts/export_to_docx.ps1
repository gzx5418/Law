param(
    [Parameter(Mandatory = $true)]
    [string]$InputMarkdown,
    [Parameter(Mandatory = $true)]
    [string]$OutputDocx
)

if (!(Test-Path $InputMarkdown)) {
    Write-Error "Input markdown not found: $InputMarkdown"
    exit 1
}

$converter = Get-Command markdown_to_docx_converter -ErrorAction SilentlyContinue
if ($converter) {
    & markdown_to_docx_converter --input "$InputMarkdown" --output "$OutputDocx"
    if ($LASTEXITCODE -eq 0) {
        Write-Output "OK: $OutputDocx"
        exit 0
    }
}

$pandoc = Get-Command pandoc -ErrorAction SilentlyContinue
if ($pandoc) {
    & pandoc "$InputMarkdown" -o "$OutputDocx"
    if ($LASTEXITCODE -eq 0) {
        Write-Output "OK: $OutputDocx"
        exit 0
    }
}

Write-Error "No available converter. Install markdown_to_docx_converter or pandoc."
exit 2

