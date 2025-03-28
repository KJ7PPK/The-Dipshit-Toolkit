# Set default path
$imgExe = "magick.exe"

# Check for .\imagemagick.exe or PATH
if (-not (Test-Path $imgExe)) {
    $foundInPath = $false
    foreach ($path in $env:PATH -split ';') {
        if ([string]::IsNullOrWhiteSpace($path)) { continue }
        $testPath = Join-Path $path "magick.exe"
        if (Test-Path $testPath) {
            $imgExe = $testPath
            $foundInPath = $true
            break
        }
    }

    if (-not $foundInPath) {
        Write-Host "`n❌ Could not find 'magick.exe' in the current folder or system PATH." -ForegroundColor Red
        Write-Host "📂 Please download ImageMagick portable and place 'magick.exe' in this directory." -ForegroundColor Yellow
        Write-Host "🔗 You can get it from:" -ForegroundColor Yellow
        Write-Host "   https://imagemagick.org/script/download.php#windows"
        Write-Host "`nThen re-run this script."
        exit
    }
}

Write-Host "🧪 Using ImageMagick from: $imgExe`n"

# HEIC → JPG conversion
$convertedCount = 0
$strippedCount = 0
$heicFiles = Get-ChildItem -Filter *.heic -Recurse

Write-Host "🔄 Starting HEIC to JPG conversion..."

if ($heicFiles.Count -eq 0) {
    Write-Host "⚠️ No HEIC files found."
} else {
    foreach ($file in $heicFiles) {
        $src = $file.FullName
        $dest = [System.IO.Path]::ChangeExtension($src, "jpg")

        try {
            Write-Host "✅ Converting: $($file.FullName)"
            & $imgExe "$src" -auto-orient -quality 92 "$dest" 2>&1 | Out-Null
            $convertedCount++
        } catch {
            Write-Warning "❌ Failed to convert $($file.FullName): $_"
        }
    }
}

# Ask to strip metadata
$stripChoice = Read-Host "`n🧼 Do you want to strip metadata from all JPGs? (Y/N)"
if ($stripChoice -match '^[Yy]') {
    $jpgFiles = Get-ChildItem -Filter *.jpg -Recurse

    if ($jpgFiles.Count -eq 0) {
        Write-Host "⚠️ No JPG files found."
    } else {
        foreach ($file in $jpgFiles) {
            $src = $file.FullName
            $tmp = "$src.tmp"

            try {
                Write-Host "🧽 Stripping metadata: $($file.FullName)"
                & $imgExe "$src" -strip "$tmp" 2>&1 | Out-Null
                Remove-Item "$src"
                Rename-Item "$tmp" "$src"
                $strippedCount++
            } catch {
                Write-Warning "❌ Failed to strip metadata from $($file.FullName): $_"
            }
        }
    }
}

# Ask to delete original HEICs
$deleteChoice = Read-Host "`n🗑️  Do you want to delete the original HEIC files? (Y/N)"
if ($deleteChoice -match '^[Yy]') {
    foreach ($file in $heicFiles) {
        try {
            Remove-Item $file.FullName -Force
            Write-Host "🗑️ Deleted: $($file.FullName)"
        } catch {
            Write-Warning "❌ Couldn't delete $($file.FullName): $_"
        }
    }
}

# 📊 Summary
Write-Host "`n🎉 Done!"
Write-Host "📸 HEIC files converted: $convertedCount"
if ($stripChoice -match '^[Yy]') {
    Write-Host "🧽 JPGs stripped of metadata: $strippedCount"
}
