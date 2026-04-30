<#
.SYNOPSIS
    Install one skill, a whole category, or a glob pattern of skills from
    github.com/mouadja02/skills without cloning the repo.

.DESCRIPTION
    Pass any of these as -Skill / -Selector:

      * an exact install path -> install one skill
            engineering-craft/test-driven-development
      * a category name       -> install every skill in that category
            engineering-craft
      * a glob pattern        -> install every install_path that matches
            "*bmad*"   "ai-agents/*"   "*-advisor"

    For single-skill mode the -Dest you pass IS the skill folder.
    For category and glob modes, -Dest is a parent folder; each matched
    skill is placed in its own subfolder underneath it.

.PARAMETER Selector
    The selector string (alias: -Skill). See DESCRIPTION.

.PARAMETER Dest
    REQUIRED. Where to install. Must not exist unless -Force is passed.
    For multi-skill installs, this is the parent folder.

.PARAMETER Branch
    Branch to install from. Default: main.

.PARAMETER Force
    Overwrite existing destinations.

.PARAMETER Flat
    Glob mode only. Place each matched skill at <Dest>\<name>\ instead
    of preserving its full install path. Errors on name collisions.

.PARAMETER DryRun
    Resolve the selector and print the install plan; do not download
    or write anything.

.PARAMETER List
    List every available skill, grouped by category. No install.

.PARAMETER ListCategories
    List every category with its skill count. No install.

.PARAMETER Help
    Show this help and exit (equivalent to Get-Help Install-Skill -Full).

.EXAMPLE
    Install-Skill engineering-craft/test-driven-development `
        -Dest $HOME\.claude\skills\test-driven-development

.EXAMPLE
    Install-Skill engineering-craft -Dest $HOME\.claude\skills\engineering-craft

.EXAMPLE
    Install-Skill "*bmad*" -Dest $HOME\.claude\skills\bmad -Flat

.EXAMPLE
    Install-Skill "ai-agents/*" -Dest $HOME\.claude\skills\ai -DryRun

.EXAMPLE
    iwr https://raw.githubusercontent.com/mouadja02/skills/main/install.ps1 -UseBasicParsing | iex
    Install-Skill --Help

.NOTES
    When piped through Invoke-Expression (`iex`), this script defines a
    global function `Install-Skill` with the same parameters as the
    script itself.
#>
[CmdletBinding(DefaultParameterSetName = 'Install')]
param(
    [Parameter(Position = 0, ParameterSetName = 'Install')]
    [Alias('Skill')]
    [string]$Selector,

    [Parameter(ParameterSetName = 'Install')]
    [Alias('d')]
    [string]$Dest,

    [Parameter(ParameterSetName = 'Install')]
    [Parameter(ParameterSetName = 'List')]
    [Parameter(ParameterSetName = 'ListCategories')]
    [string]$Branch = 'main',

    [Parameter(ParameterSetName = 'Install')]
    [switch]$Force,

    [Parameter(ParameterSetName = 'Install')]
    [switch]$Flat,

    [Parameter(ParameterSetName = 'Install')]
    [switch]$DryRun,

    [Parameter(ParameterSetName = 'List')]
    [switch]$List,

    [Parameter(ParameterSetName = 'ListCategories')]
    [switch]$ListCategories,

    [Parameter(ParameterSetName = 'Help')]
    [Alias('h')]
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

function Install-Skill {
<#
.SYNOPSIS
    Install one skill, a whole category, or a glob pattern of skills.

.DESCRIPTION
    See `Install-Skill -Help` for full documentation. Selectors:
      * exact install path -> single skill
      * category name      -> all skills in category
      * pattern with * / ? -> glob match against install_path
#>
    [CmdletBinding(DefaultParameterSetName = 'Install')]
    param(
        [Parameter(Position = 0, ParameterSetName = 'Install')]
        [Alias('Skill')]
        [string]$Selector,

        [Parameter(ParameterSetName = 'Install')]
        [Alias('d')]
        [string]$Dest,

        [string]$Branch = 'main',

        [Parameter(ParameterSetName = 'Install')]
        [switch]$Force,

        [Parameter(ParameterSetName = 'Install')]
        [switch]$Flat,

        [Parameter(ParameterSetName = 'Install')]
        [switch]$DryRun,

        [Parameter(ParameterSetName = 'List')]
        [switch]$List,

        [Parameter(ParameterSetName = 'ListCategories')]
        [switch]$ListCategories,

        [Parameter(ParameterSetName = 'Help')]
        [Alias('h')]
        [switch]$Help
    )

    $repo = if ($env:SKILLS_REPO) { $env:SKILLS_REPO } else { 'mouadja02/skills' }
    $rawBase = if ($env:SKILLS_RAW_BASE) { $env:SKILLS_RAW_BASE } else { "https://raw.githubusercontent.com/$repo" }
    $tarballBase = if ($env:SKILLS_TARBALL_BASE) { $env:SKILLS_TARBALL_BASE } else { "https://codeload.github.com/$repo/tar.gz/refs/heads" }
    $tarballUrl = "$tarballBase/$Branch"
    $manifestUrl = "$rawBase/$Branch/docs/manifest.json"

    if ($Help) {
        Get-Help Install-Skill -Full
        return
    }

    if ($List -or $ListCategories) {
        $manifest = Invoke-RestMethod -Uri $manifestUrl -UseBasicParsing
        if ($ListCategories) {
            $manifest.skills |
                Group-Object category |
                Sort-Object Name |
                ForEach-Object {
                    [pscustomobject]@{ Category = $_.Name; Count = $_.Count }
                } |
                Format-Table -AutoSize
        } else {
            $manifest.skills |
                Sort-Object install_path |
                ForEach-Object {
                    [pscustomobject]@{
                        Category    = $_.category
                        InstallPath = $_.install_path
                    }
                } |
                Format-Table -AutoSize
        }
        return
    }

    if (-not $Selector) { throw "Missing -Selector / -Skill (try -Help)" }
    if (-not $Dest)     { throw "Missing -Dest" }
    if ($Selector.StartsWith('/') -or $Selector.Contains('..')) {
        throw "Invalid selector: $Selector"
    }

    if (-not (Get-Command tar -ErrorAction SilentlyContinue)) {
        throw "tar.exe is required (built into Windows 10 1803+ and PowerShell Core)."
    }

    Write-Host "==> Fetching manifest from $repo@$Branch" -ForegroundColor Cyan
    $manifest = Invoke-RestMethod -Uri $manifestUrl -UseBasicParsing

    # --- Resolve selector ----------------------------------------------------
    $mode = $null
    $cat = $null
    $selected = @()

    if ($Selector -match '[\*\?]') {
        $mode = 'glob'
        $selected = @($manifest.skills | Where-Object { $_.install_path -like $Selector })
        if (-not $selected) { throw "no install_path matches pattern: $Selector  (try -List)" }
    } else {
        $exact = $manifest.skills | Where-Object { $_.install_path -eq $Selector }
        if ($exact) {
            $mode = 'single'
            $selected = @($exact)
        } else {
            $catMatches = @($manifest.skills | Where-Object { $_.category -eq $Selector })
            if ($catMatches) {
                $mode = 'category'
                $cat = $Selector
                $selected = $catMatches
            } else {
                throw "no skill, category, or pattern matches: $Selector  (try -List or -ListCategories)"
            }
        }
    }

    Write-Host "==> Selector matched $($selected.Count) skill(s) in mode '$mode'" -ForegroundColor Cyan

    # --- Plan destinations and detect collisions -----------------------------
    $plan = New-Object System.Collections.Generic.List[object]
    $seen = New-Object System.Collections.Generic.HashSet[string]
    foreach ($s in $selected) {
        $ip = $s.install_path
        switch ($mode) {
            'single'   { $target = $Dest }
            'category' { $target = Join-Path $Dest ($ip.Substring($cat.Length + 1)) }
            'glob' {
                if ($Flat) {
                    $target = Join-Path $Dest (Split-Path $ip -Leaf)
                } else {
                    # Cross-platform: use forward-slash splits, then rejoin.
                    $target = Join-Path $Dest ($ip -replace '/', [IO.Path]::DirectorySeparatorChar)
                }
            }
        }
        $normalized = [IO.Path]::GetFullPath($target)
        if (-not $seen.Add($normalized)) {
            throw "destination collision: '$target' resolves from two skills (drop -Flat or narrow the selector)"
        }
        if ((Test-Path -LiteralPath $target) -and -not $Force) {
            throw "destination already exists: $target  (use -Force to overwrite)"
        }
        $plan.Add([pscustomobject]@{ InstallPath = $ip; Target = $target })
    }

    if ($DryRun) {
        Write-Host "==> Dry run: would install:" -ForegroundColor Cyan
        $plan | ForEach-Object {
            "  {0,-50} -> {1}" -f $_.InstallPath, $_.Target
        }
        return
    }

    # --- Download tarball ----------------------------------------------------
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("skills-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $tarball = Join-Path $tmp 'repo.tar.gz'
    $extract = Join-Path $tmp 'extract'
    New-Item -ItemType Directory -Force -Path $extract | Out-Null

    try {
        Write-Host "==> Downloading $repo@$Branch tarball" -ForegroundColor Cyan
        Invoke-WebRequest -Uri $tarballUrl -OutFile $tarball -UseBasicParsing

        Write-Host "==> Extracting" -ForegroundColor Cyan
        $prevErrAction = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & tar -xzf $tarball -C $extract
            if ($LASTEXITCODE -ne 0) { throw "tar failed with exit code $LASTEXITCODE" }
        } finally {
            $ErrorActionPreference = $prevErrAction
        }

        $repoName = $repo.Split('/')[-1]
        $topDir = Join-Path $extract "$repoName-$Branch"
        $skillsRoot = Join-Path $topDir 'skills'
        if (-not (Test-Path -LiteralPath $skillsRoot)) {
            throw "Unexpected tarball layout: $skillsRoot not found"
        }

        Write-Host "==> Installing $($plan.Count) skill(s)" -ForegroundColor Cyan
        foreach ($entry in $plan) {
            $src = Join-Path $skillsRoot ($entry.InstallPath -replace '/', [IO.Path]::DirectorySeparatorChar)
            if (-not (Test-Path -LiteralPath $src)) {
                throw "missing in tarball: skills/$($entry.InstallPath)"
            }
            if ((Test-Path -LiteralPath $entry.Target) -and $Force) {
                Remove-Item -LiteralPath $entry.Target -Recurse -Force
            }
            # Use .NET directly: Split-Path -LiteralPath -Parent has a known
            # AmbiguousParameterSet bug in some Windows PowerShell versions.
            $parent = [System.IO.Path]::GetDirectoryName($entry.Target)
            if ($parent -and -not (Test-Path -LiteralPath $parent)) {
                New-Item -ItemType Directory -Force -Path $parent | Out-Null
            }
            Copy-Item -LiteralPath $src -Destination $entry.Target -Recurse -Force
            Write-Host "  - $($entry.InstallPath) -> $($entry.Target)"
        }

        Write-Host "==> Done. Installed $($plan.Count) skill(s) under $Dest" -ForegroundColor Green
    }
    finally {
        Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# If any parameter was bound (script invoked with args), dispatch now.
# If no parameters were bound (e.g. piped through `iex` with no args), this
# block is skipped and the caller is expected to invoke `Install-Skill`.
if ($PSBoundParameters.Count -gt 0) {
    $invokeParams = @{ Branch = $Branch }
    switch ($PSCmdlet.ParameterSetName) {
        'Install' {
            if ($Selector) { $invokeParams['Selector'] = $Selector }
            if ($Dest)     { $invokeParams['Dest']     = $Dest }
            if ($Force)    { $invokeParams['Force']    = $true }
            if ($Flat)     { $invokeParams['Flat']     = $true }
            if ($DryRun)   { $invokeParams['DryRun']   = $true }
        }
        'List'           { $invokeParams['List'] = $true }
        'ListCategories' { $invokeParams['ListCategories'] = $true }
        'Help'           { $invokeParams['Help'] = $true }
    }
    Install-Skill @invokeParams
}
