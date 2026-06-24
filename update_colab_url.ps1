# ============================================================
# VAX Studio — Update Colab Engine URL
# Jalankan script ini setiap kali Colab di-restart
# Usage: .\update_colab_url.ps1
# ============================================================

$newUrl = Read-Host "Masukkan URL Colab baru (dari output '📡 URL:')"

if ($newUrl -match "^https://") {
    $envPath = "$PSScriptRoot\.env"
    $content = Get-Content $envPath -Raw
    $content = $content -replace "COLAB_API_URL=.*", "COLAB_API_URL=$newUrl"
    Set-Content $envPath $content -NoNewline
    Write-Host "`n✅ URL berhasil diupdate: $newUrl" -ForegroundColor Green
    Write-Host "⚠️  Restart server (start_server.bat) agar perubahan aktif.`n" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ URL tidak valid. Harus diawali dengan 'https://'" -ForegroundColor Red
}
