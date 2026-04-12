param(
  [string]$BackendUrl = "http://localhost:18000",
  [string]$UserId = "default",
  [string]$SkillName = "legal-copilot"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillDir = Split-Path -Parent $scriptDir
$zipPath = Join-Path (Split-Path -Parent $skillDir) "legal-copilot-portable.zip"

Write-Host "[1/4] Running health check..."
python (Join-Path $scriptDir "health_check.py") | Out-Null

Write-Host "[2/4] Packing skill..."
python (Join-Path $scriptDir "pack_skill_zip.py") --skill-dir $skillDir --out $zipPath | Out-Null

Write-Host "[3/4] Discovering import candidates..."
$discoverRaw = curl.exe -sS -X POST "$BackendUrl/api/v1/skills/import/discover" -H "X-User-Id: $UserId" -F "file=@$zipPath"
$discover = $discoverRaw | ConvertFrom-Json
if (-not $discover.data.archive_key) {
  throw "Discover failed: $discoverRaw"
}

$commitBody = @{
  archive_key = $discover.data.archive_key
  selections = @(@{ relative_path = "."; name_override = $SkillName })
} | ConvertTo-Json -Depth 10

$commit = Invoke-RestMethod -Method Post -Uri "$BackendUrl/api/v1/skills/import/commit" -Headers @{
  "X-User-Id" = $UserId
  "Content-Type" = "application/json; charset=utf-8"
} -Body $commitBody

$jobId = $commit.data.job_id
if (-not $jobId) {
  throw "Commit failed: missing job id"
}

Write-Host "[4/4] Waiting import job: $jobId"
$deadline = (Get-Date).AddSeconds(60)
$job = $null
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Milliseconds 700
  $job = Invoke-RestMethod -Method Get -Uri "$BackendUrl/api/v1/skills/import/jobs/$jobId" -Headers @{ "X-User-Id" = $UserId }
  if ($job.data.status -in @("success", "failed")) { break }
}

if (-not $job) { throw "Import job polling failed." }

$item = $job.data.result.items[0]
[pscustomobject]@{
  job_id = $jobId
  status = $job.data.status
  skill_id = $item.skill_id
  skill_name = $item.skill_name
  overwritten = $item.overwritten
} | ConvertTo-Json -Depth 8

