# Drive the game in RPCS3 with the default keyboard pad mapping, then screenshot.
# Usage: powershell -File rpcs3_input.ps1 -Keys "X,wait2,DOWN,X" [-Shot]
#   Buttons: X (Cross) C (Circle) Z (Square) V (Triangle) START SELECT UP DOWN LEFT RIGHT L1 R1 R2
#   A+B presses B while A is held (e.g. R1+START = skip dialogue in Moon Dwellers).
#   waitN = sleep N seconds. Prints the screenshot path when -Shot is given.
param([string]$Keys = "", [switch]$Shot, [string]$Serial = "BLJS10335")
Add-Type -Name K -Namespace W -MemberDefinition '[DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);'
$map = @{ X=0x58; C=0x43; Z=0x5A; V=0x56; START=0x0D; SELECT=0x20; UP=0x26; DOWN=0x28; LEFT=0x25; RIGHT=0x27; F12=0x7B; L1=0x51; R1=0x45; R2=0x54 }
$ws = New-Object -ComObject WScript.Shell
$null = $ws.AppActivate("FPS:")
Start-Sleep -Milliseconds 500
function Press($vk) {
    $ext = 0; if ($vk -ge 0x25 -and $vk -le 0x28) { $ext = 1 }   # arrows: extended keys, else they read as numpad
    [W.K]::keybd_event($vk, 0, $ext, [UIntPtr]::Zero); Start-Sleep -Milliseconds 120
    [W.K]::keybd_event($vk, 0, ($ext -bor 2), [UIntPtr]::Zero); Start-Sleep -Milliseconds 350
}
foreach ($k in ($Keys -split ',')) {
    $k = $k.Trim().ToUpper()
    if ($k -eq '') { continue }
    if ($k -like 'WAIT*') { Start-Sleep -Seconds ([double]$k.Substring(4)); continue }
    if ($k -eq 'RESUME') {   # RPCS3 pauses on focus loss; resume = hold START ~2 s
        [W.K]::keybd_event($map['START'], 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 2200
        [W.K]::keybd_event($map['START'], 0, 2, [UIntPtr]::Zero); Start-Sleep -Milliseconds 500; continue
    }
    if ($k -like '*+*') {   # chord: hold the first, press the second
        $h, $p = $k -split '\+', 2
        [W.K]::keybd_event($map[$h], 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 150
        Press $map[$p]
        [W.K]::keybd_event($map[$h], 0, 2, [UIntPtr]::Zero); Start-Sleep -Milliseconds 300; continue
    }
    if (-not $map.ContainsKey($k)) { Write-Error "unknown key $k"; exit 1 }
    Press $map[$k]
}
if ($Shot) {
    $dir = "$env:USERPROFILE\RPCS3\screenshots\$Serial"
    $before = (Get-ChildItem $dir -ErrorAction SilentlyContinue | Measure-Object).Count
    Press $map['F12']
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 250
        if ((Get-ChildItem $dir | Measure-Object).Count -gt $before) { break }
    }
    (Get-ChildItem $dir | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
}
