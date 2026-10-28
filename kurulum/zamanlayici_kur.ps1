# Taramayı Windows Görev Zamanlayıcı'ya ekler: saatte bir "python main.py --schedule" uyanır
# (tarama -> ajan analizi -> maliyet ve alarmlar). Bilgisayar açılınca da çalışmaya devam eder.
# Taramanın kaç saatte bir yapılacağı panelin Ayarlar sayfasından seçilir (app_settings): main.py son başarılı
# taramadan o kadar süre geçmediyse taramadan çıkar. -Saat yalnızca uyanma aralığıdır.
#
#   .\kurulum\zamanlayici_kur.ps1                    # kur
#   .\kurulum\zamanlayici_kur.ps1 -Saat 0.5          # yarım saatte bir uyan (panelde seçilen aralık yine geçerli)
#   .\kurulum\zamanlayici_kur.ps1 -OturumKapaliyken  # oturum kapalıyken de çalışsın (yönetici PowerShell)
#   .\kurulum\zamanlayici_kur.ps1 -Kaldir            # görevi sil
#
# Çıktılar logs\tarama.log dosyasına eklenir. Görev varsayılan olarak oturum açıkken (kilitliyken de)
# masaüstünde, pencere açmadan çalışır; böylece windows:// bildirimleri görünür. -OturumKapaliyken
# ile (S4U) oturum kapalıyken de çalışır ama masaüstüne erişemez, windows:// bildirimleri görünmez.

param(
    [double]$Saat = 1,
    [switch]$OturumKapaliyken,
    [switch]$Kaldir
)

$ErrorActionPreference = "Stop"
$GorevAdi = "SupplyChain Tarama"

if ($Kaldir) {
    Unregister-ScheduledTask -TaskName $GorevAdi -Confirm:$false
    Write-Host "Görev silindi: $GorevAdi"
    return
}

$Kok = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Kok ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $Python)) { throw "Sanal ortam bulunamadı: $Python (önce .venv kurun)" }
if (-not (Test-Path (Join-Path $Kok ".env"))) { throw ".env bulunamadı (kökteki .env.example'dan kopyalayın)" }
New-Item -ItemType Directory -Force (Join-Path $Kok "logs") | Out-Null

# pythonw konsol penceresi açmaz; çıktıyı Python kendisi log dosyasına (UTF-8) yazar
$Kod = "import runpy,sys; sys.stdout=sys.stderr=open('logs/tarama.log','a',encoding='utf-8',buffering=1); " +
       "sys.argv=['main.py','--schedule']; runpy.run_path('main.py',run_name='__main__')"
$Eylem = New-ScheduledTaskAction -Execute $Python -Argument "-c `"$Kod`"" -WorkingDirectory $Kok

# Kurulumdan 1 dakika sonra başlar, sonra her $Saat saatte bir tekrar eder (süresiz)
$Tetik = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes ([int]($Saat * 60)))

# Uzun süren bir tarama bitmeden yenisi başlamaz; kaçırılan çalışma bilgisayar açılınca yapılır
$Ayar = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 10) `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

$Oturum = if ($OturumKapaliyken) { "S4U" } else { "Interactive" }
$Kullanici = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType $Oturum

Register-ScheduledTask -TaskName $GorevAdi -Action $Eylem -Trigger $Tetik -Settings $Ayar -Principal $Kullanici `
    -Description "Tedarik zinciri haber taraması + ajan analizi + alarmlar (main.py --schedule)" -Force | Out-Null

Write-Host "Görev kuruldu: $GorevAdi (her $Saat saatte bir uyanır, ilk çalışma 1 dakika sonra, oturum: $Oturum)"
Write-Host "Tarama aralığı panelin Ayarlar sayfasından seçilir (varsayılan 3 saat)."
Write-Host "Log: $Kok\logs\tarama.log"
Write-Host "Hemen çalıştır: Start-ScheduledTask -TaskName '$GorevAdi'"
