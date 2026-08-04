"""
=============================================================================
Genera los íconos que necesita la app de Google Play (TWA).
=============================================================================
Se corre a mano, cuando cambia el dibujo de la app. NO forma parte del
servidor: PythonAnywhere sirve imágenes, no las fabrica. Por eso Pillow vive
en requirements-dev.txt y no en requirements.txt.

    venv\\Scripts\\python.exe herramientas\\generar_iconos.py

QUÉ PROBLEMA RESUELVE
---------------------
El dibujo de la mamá con el bebé está "a sangre": el pelo toca el borde de
arriba y de la izquierda, y el body del bebé toca el de abajo a la derecha.
Android, para hacer el ícono redondo, recorta hasta el 20% de cada lado — o
sea que se comía pelo y bebé.

La solución es la que manda la especificación de íconos "maskable": el dibujo
entra al 80% y el 20% que sobra es marco de relleno. Todo lo importante (las
dos caras) queda adentro del círculo que Android nunca toca.

POR QUÉ EL RELLENO SE MUESTREA DE LA ESQUINA SUPERIOR DERECHA
-------------------------------------------------------------
La tentación es promediar los cuatro bordes del dibujo. Acá NO funciona: los
bordes no son parejos (arriba es el marrón del pelo, abajo el blanco de la
ropa, a la derecha el azul del body). El promedio de los cuatro da un marrón
sucio —medido: (164,145,129) arriba— que se vería como un marco embarrado.

La esquina superior derecha, en cambio, es fondo limpio de la ilustración:
(252,242,227). Rellenar con ESE color hace que el marco se funda sin costura
con toda la mitad de arriba del dibujo.
=============================================================================
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageStat

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONOS = os.path.join(RAIZ, 'static', 'icons')
TIENDA = os.path.join(RAIZ, 'tienda')

ORIGEN = os.path.join(ICONOS, 'icon-512.png')

LADO = 512
# Android puede recortar hasta el 20% de cada lado para armar el ícono redondo.
ZONA_SEGURA = 0.8
# Redondeo y desenfoque del borde del dibujo pegado. Sin esto se ve el canto
# recto del cuadrado contra el crema, que delata el pegote.
RADIO = 48
DESENFOQUE = 4

# Medidas que pide Google Play para la ficha de la tienda.
BANNER = (1024, 500)


def color_de_fondo(im):
    """El crema limpio del dibujo, muestreado de la esquina superior derecha.

    Ver el encabezado: promediar los cuatro bordes daría un marrón sucio."""
    muestra = im.crop((im.width - 112, 0, im.width, 60)).convert('RGB')
    return tuple(int(canal) for canal in ImageStat.Stat(muestra).mean)


def dibujo_con_bordes_suaves(im, lado):
    """El dibujo escalado, con las esquinas redondeadas y el canto desvanecido.

    Devuelve (imagen, máscara) para pegarlo sobre el fondo."""
    escalado = im.resize((lado, lado), Image.LANCZOS)
    mascara = Image.new('L', (lado, lado), 0)
    ImageDraw.Draw(mascara).rounded_rectangle(
        (0, 0, lado - 1, lado - 1), radius=RADIO, fill=255)
    return escalado, mascara.filter(ImageFilter.GaussianBlur(DESENFOQUE))


def componer(fuente, fondo, lado_lienzo, lado_dibujo):
    """Lienzo del color de fondo con el dibujo centrado encima."""
    lienzo = Image.new('RGB', (lado_lienzo, lado_lienzo), fondo)
    dibujo, mascara = dibujo_con_bordes_suaves(fuente, lado_dibujo)
    borde = (lado_lienzo - lado_dibujo) // 2
    lienzo.paste(dibujo, (borde, borde), mascara)
    return lienzo


def generar_banner(compuesto, fondo):
    """El "gráfico destacado" de la ficha de Play: 1024x500, obligatorio.

    Va sin texto a propósito: las fuentes de la app son .woff2 y Pillow no las
    sabe leer, así que escribir "Lactancia" con cualquier otra tipografía
    rompería la identidad visual. Play igual muestra el nombre de la app
    encima del gráfico.

    El dibujo va CENTRADO y no a un costado porque Play recorta este gráfico
    distinto según dónde lo muestre; centrado no hay recorte que lo arruine.

    Se reusa la composición del ícono —la que ya tiene el marco crema— y se
    pega SIN máscara: como su borde es exactamente el mismo crema del lienzo,
    la unión es invisible. El primer intento recortaba el dibujo en círculo y
    quedaba un canto duro donde el pelo se cortaba de golpe."""
    ancho, alto = BANNER
    lienzo = Image.new('RGB', BANNER, fondo)
    lado = int(alto * 0.94)
    lienzo.paste(compuesto.resize((lado, lado), Image.LANCZOS),
                 ((ancho - lado) // 2, (alto - lado) // 2))
    return lienzo


def main():
    fuente = Image.open(ORIGEN).convert('RGB')
    if fuente.size != (LADO, LADO):
        raise SystemExit(f'{ORIGEN} debería ser {LADO}x{LADO} y es {fuente.size}')

    fondo = color_de_fondo(fuente)
    print(f'Relleno muestreado del dibujo: RGB{fondo}')

    util = round(LADO * ZONA_SEGURA)
    compuesto = componer(fuente, fondo, LADO, util)

    os.makedirs(TIENDA, exist_ok=True)

    # 1) El del manifiesto. Va en RGB (opaco): el ícono maskable cubre todo el
    #    lienzo por definición, un canal alfa solo sumaría peso.
    salida = os.path.join(ICONOS, 'icon-512-maskable.png')
    compuesto.save(salida, 'PNG', optimize=True)
    print(f'OK  {salida}  ({util}x{util} de dibujo sobre {LADO}x{LADO})')

    # 2) El de la ficha de Play. RGBA porque Play Console RECHAZA los PNG de 24
    #    bits: pide 32 bits con canal alfa. Los cuatro íconos del repo son RGB,
    #    así que subir icon-512.png directo al Console falla.
    salida = os.path.join(TIENDA, 'icono-play-512.png')
    compuesto.convert('RGBA').save(salida, 'PNG', optimize=True)
    print(f'OK  {salida}  (RGBA, como exige Play Console)')

    # 3) El gráfico destacado de la ficha.
    salida = os.path.join(TIENDA, 'grafico-destacado-1024x500.png')
    generar_banner(compuesto, fondo).save(salida, 'PNG', optimize=True)
    print(f'OK  {salida}  ({BANNER[0]}x{BANNER[1]})')


if __name__ == '__main__':
    main()
