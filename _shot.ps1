param([string]$Role = "", [string]$Out = "shot.png", [string]$Inject = "", [string]$Size = "1280,800")
# Scratch helper: screenshot ics-os.html in headless Edge. Role "" = no session (boot/login).
$h = Get-Content "$PSScriptRoot\ics-os.html" -Raw -Encoding UTF8
$i = $h.IndexOf('<script')
$pre = ""
if ($Role) { $pre = '<script>sessionStorage.setItem("icsos", JSON.stringify({role:"' + $Role + '"}));</script>' }
else { $pre = '<script>try{localStorage.clear();sessionStorage.clear();}catch(e){}</script>' }
$post = ""
if ($Inject) { $post = "<script>window.addEventListener('load',function(){setTimeout(function(){ $Inject },2500)});</script></body>" }
$h2 = $h.Insert($i, $pre)
if ($post) { $h2 = $h2.Replace('</body>', $post) }
$f = "$env:TEMP\shot_in.html"
[IO.File]::WriteAllText($f, $h2, (New-Object Text.UTF8Encoding $false))
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
Start-Process $edge -ArgumentList '--headless=new','--disable-gpu',"--window-size=$Size",'--virtual-time-budget=12000',"--screenshot=$Out","--user-data-dir=$env:TEMP\edgeprof_s","file:///$($f.Replace('\','/'))" -RedirectStandardError "$env:TEMP\shot_err.txt" -Wait
taskkill /F /IM msedge.exe 2>$null | Out-Null
Remove-Item $f -ErrorAction SilentlyContinue
