<#
=============================================================================
 vigilar_sitio.ps1 - Avisa si la app de Lactancia se cayo.
=============================================================================
 POR QUE EXISTE
 --------------
 La cuenta gratis de PythonAnywhere se APAGA SOLA cada mes si nadie inicia
 sesion y aprieta el boton "Run until 1 month from today". Cuando eso pasa, la
 app no da error: el servidor devuelve una pagina que dice "Coming Soon", como
 si el sitio no existiera. Nadie se entera hasta que alguna mama escribe.
 Paso el 26/08/2026 y estuvo caida sin que lo supieramos.

 ESTO NO RENUEVA NADA. No se puede: PythonAnywhere pide una persona iniciando
 sesion a proposito, y automatizarlo obligaria a dejar la contrasena escrita en
 un archivo. Esto solo MIRA y AVISA.

 SE USA ASI (lo corren solas las dos tareas programadas de Windows):
   powershell -File vigilar_sitio.ps1                 -> revisa y avisa si esta caida
   powershell -File vigilar_sitio.ps1 -Recordatorio   -> recuerda renovar, sin revisar
=============================================================================
#>
param(
    # Modo recordatorio: no revisa nada, solo avisa que toca renovar.
    [switch]$Recordatorio
)

$URL      = 'https://paralasmamas.pythonanywhere.com/bienvenida'
$PANEL    = 'https://www.pythonanywhere.com/user/paralasmamas/webapps/'
$REGISTRO = Join-Path $PSScriptRoot 'vigilancia.log'

function Anotar($texto) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm')  $texto" | Add-Content -Path $REGISTRO -Encoding utf8
}

function Avisar($titulo, $texto) {
    # Un cartel que se queda hasta que lo cierres. Es a proposito: un globito de
    # notificacion se desvanece solo y este aviso no se puede perder.
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show(
        $texto, $titulo,
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Warning) | Out-Null
}

$PASOS = @"

Para revertirlo:
  1. Entra a $PANEL
  2. Boton amarillo "Run until 1 month from today"
  3. Boton verde "Reload"
"@

$AVISO_VENCIDA = @"
La app no esta funcionando. Las mamas que entren ahora no la ven.

Se vencio la cuenta gratis de PythonAnywhere.
$PASOS
"@

if ($Recordatorio) {
    Anotar 'RECORDATORIO mostrado'
    Avisar 'Lactancia - toca renovar el sitio' @"
La cuenta gratis de PythonAnywhere se apaga sola cada mes.

Entra a renovarla AHORA, antes de que se venza, asi la app no se
cae para las mamas que la usan.
$PASOS
"@
    exit 0
}

# --- Revision de verdad -----------------------------------------------------
# Se pide la pantalla de bienvenida y no la raiz: la raiz redirige, y un
# redirect puede contestar bien aunque la app este mal.
try {
    $r = Invoke-WebRequest -Uri $URL -TimeoutSec 30 -UseBasicParsing -ErrorAction Stop
} catch {
    # Ojo: en Windows PowerShell 5.1 un 404 no llega abajo, llega ACA como
    # excepcion. El 404 es justamente la pagina "Coming Soon" del vencimiento.
    $codigo = $null
    if ($_.Exception.Response) { $codigo = [int]$_.Exception.Response.StatusCode }
    if ($codigo -eq 404) {
        Anotar 'CAIDA - HTTP 404, la cuenta gratis se vencio'
        Avisar 'Lactancia - LA APP ESTA CAIDA' $AVISO_VENCIDA
    } else {
        Anotar "CAIDA - no contesto: $($_.Exception.Message)"
        Avisar 'Lactancia - LA APP NO CONTESTA' @"
La app no contesta.

Detalle tecnico: $($_.Exception.Message)

Puede ser que se haya vencido la cuenta gratis de PythonAnywhere,
o que ahora mismo vos no tengas internet. Fijate primero si podes
abrir cualquier otra pagina.
$PASOS
"@
    }
    exit 1
}

# Cinturon y tiradores, por si algun dia contesta 200 con la pagina del hosting.
if ($r.StatusCode -ne 200 -or $r.Content -match 'Coming Soon') {
    Anotar "CAIDA - HTTP $($r.StatusCode) con pagina del hosting"
    Avisar 'Lactancia - LA APP ESTA CAIDA' $AVISO_VENCIDA
    exit 1
}

# Que sea NUESTRA pantalla y no cualquier pagina con codigo 200 (una de
# mantenimiento del hosting, por ejemplo). "lac-" es el prefijo de las clases
# de la app: si eso no esta, lo que volvio no es la bienvenida.
if ($r.Content -notmatch 'lac-') {
    Anotar 'RARO - contesta 200 pero no parece la app'
    Avisar 'Lactancia - algo raro' @"
El sitio contesta, pero lo que devuelve no parece la app.

Conviene abrirlo y mirarlo:
$URL
"@
    exit 1
}

Anotar 'OK'
exit 0
