function Show-Tree {
    param([string]$Path = ".", [int]$Level = 0, [int]$MaxDepth = 10)

    if ($Level -gt $MaxDepth) { return }
    $Prefix = ("|   " * $Level) + "|-- "
    Get-ChildItem $Path -Exclude ".idea", ".venv" | ForEach-Object {
        Write-Output "$Prefix$($_.Name)"
        if ($_.PsIsContainer) {
            Show-Tree -Path $_.FullName -Level ($Level + 1) -MaxDepth $MaxDepth
        }
    }
}

Show-Tree