from flask import Flask, render_template, request, redirect, url_for # Para manejar la aplicación web
import os # Para manejar archivos y carpetas
import json # Para manejar archivos JSON
from datetime import datetime # Para obtener la fecha y hora actual
import base64 # Para decodificar la imagen de la cámara
import re # Para expresiones regulares
from flask import Flask, render_template, request, redirect, url_for, send_file # Para manejar la aplicación web
from reportlab.lib.pagesizes import letter # Para el tamaño de la página
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle # Para los estilos del PDF
from reportlab.lib import colors # Para los colores del PDF
from reportlab.lib.units import inch # Para las unidades de medida
from reportlab.platypus import PageBreak # Para los saltos de página
from collections import defaultdict # Para manejar los datos de los hijos
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak # Para crear el PDF
from io import BytesIO # Para manejar los bytes de la imagen


app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

USUARIO_ADMIN = "admin"
CONTRASENA_ADMIN = "adentro"

DATABASE_FOLDER = 'C:\\data_base'

if not os.path.exists(DATABASE_FOLDER):
    os.makedirs(DATABASE_FOLDER)
    print(f"Carpeta de base de datos creada en: {DATABASE_FOLDER}")

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        if usuario == USUARIO_ADMIN and contrasena == CONTRASENA_ADMIN:
            return redirect(url_for('dashboard'))
        else:
            error = 'Usuario o contraseña incorrectos'
    return render_template('index.html', error=error)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/cargar_trabajador', methods=['GET'])
def cargar_trabajador():
    return render_template('cargar_trabajador.html')

@app.route('/editar_trabajador', methods=['GET', 'POST'])
@app.route('/editar_trabajador', methods=['GET', 'POST'])
def editar_trabajador():
    mensaje_error = None
    mensaje_exito = None
    trabajador_data = None
    cedula_buscar = None

    print("Entrando a la función editar_trabajador")

    if request.method == 'POST':
        print("Método POST recibido")
        cedula_buscar = request.form.get('cedula_buscar')
        print(f"Cédula buscada: {cedula_buscar}")
        if cedula_buscar:
            filepath = os.path.join(DATABASE_FOLDER, f"{cedula_buscar}.json")
            print(f"Ruta del archivo: {filepath}")
            if os.path.exists(filepath):
                print("El archivo existe")
                try:
                    with open(filepath, 'r') as f:
                        trabajador_data = json.load(f)
                    mensaje_exito = "Éxito: Datos del trabajador recuperados."
                    print("Datos cargados exitosamente")
                    return render_template('editar_trabajador_form.html', trabajador=trabajador_data, cedula_buscar=cedula_buscar, mensaje_exito=mensaje_exito)
                except json.JSONDecodeError:
                    mensaje_error = "Error al decodificar el archivo JSON."
                    print(f"Error JSONDecodeError: {mensaje_error}")
                except Exception as e:
                    mensaje_error = f"Error al leer el archivo: {str(e)}"
                    print(f"Error al leer el archivo: {mensaje_error}")
            else:
                mensaje_error = "La cédula no pertenece a ningún trabajador."
                print(f"Error: Cédula no encontrada: {mensaje_error}")
        else:
            mensaje_error = "No se recibió la cédula en el formulario."
            print(f"Error: No se recibió cédula: {mensaje_error}")
    else:
        print("Método GET recibido")

    return render_template('editar_trabajador.html', trabajador=trabajador_data, cedula_buscar=cedula_buscar, mensaje_exito=mensaje_exito)

@app.route('/guardar_trabajador', methods=['POST'])
def guardar_trabajador():
    if request.method == 'POST':
        trabajador_data = request.form.to_dict()
        cedula = trabajador_data.get('cedula')
        if not cedula:
            return "Error: La cédula del trabajador es obligatoria.", 400

        filename = f"{cedula}.json"
        filepath = os.path.join(DATABASE_FOLDER, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(trabajador_data, f, indent=4, ensure_ascii=False)
            return "Datos del trabajador guardados exitosamente."
        except Exception as e:
            return f"Error al guardar los datos: {str(e)}", 500
    return redirect(url_for('cargar_trabajador'))

@app.route('/actualizar_trabajador', methods=['POST'])
def actualizar_trabajador():
    if request.method == 'POST':
        trabajador_data = request.form.to_dict()
        cedula_original = trabajador_data.get('cedula_original')
        if not cedula_original:
            return "Error: La cédula original del trabajador es obligatoria.", 400

        filename = f"{cedula_original}.json"
        filepath = os.path.join(DATABASE_FOLDER, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(trabajador_data, f, indent=4, ensure_ascii=False)
            return "Datos del trabajador actualizados exitosamente."
        except Exception as e:
            return f"Error al actualizar los datos: {str(e)}", 500
    return redirect(url_for('editar_trabajador'))

@app.route('/cargar_fotografia', methods=['GET', 'POST'])
def cargar_fotografia():
    mensaje = None
    if request.method == 'POST':
        if 'foto_archivo' in request.files and request.files['foto_archivo'].filename != '':
            foto_archivo = request.files['foto_archivo']
            cedula = request.form.get('cedula_foto_archivo')
            if cedula:
                filename = f"{cedula}_foto.png"  # Guarda con la cédula como nombre
                filepath = os.path.join(DATABASE_FOLDER, "fotos", filename)
                if not os.path.exists(os.path.join(DATABASE_FOLDER, "fotos")):
                    os.makedirs(os.path.join(DATABASE_FOLDER, "fotos"))
                try:
                    foto_archivo.save(filepath)
                    mensaje = f"Fotografía cargada exitosamente para la cédula: {cedula} (desde archivo)."
                except Exception as e:
                    mensaje = f"Error al guardar la fotografía: {str(e)}"
            else:
                mensaje = "Error: No se proporcionó la cédula para la fotografía cargada desde archivo."
        elif 'foto_capturada' in request.form:
            foto_data = request.form['foto_capturada']
            cedula = request.form.get('cedula_foto_camara')
            if cedula and foto_data:
                try:
                    image_str = re.search(r'base64,(.*)', foto_data).group(1)
                    image_bytes = base64.b64decode(image_str)
                    filename = f"{cedula}_camara.png"
                    filepath = os.path.join(DATABASE_FOLDER, "fotos", filename)
                    if not os.path.exists(os.path.join(DATABASE_FOLDER, "fotos")):
                        os.makedirs(os.path.join(DATABASE_FOLDER, "fotos"))
                    with open(filepath, 'wb') as f:
                        f.write(image_bytes)
                    mensaje = f"Fotografía capturada desde la cámara y guardada para la cédula: {cedula}."
                except Exception as e:
                    mensaje = f"Error al guardar la fotografía capturada: {str(e)}"
            else:
                mensaje = "Error: No se proporcionó la cédula o los datos de la cámara."
        else:
            mensaje = "No se seleccionó ningún archivo o no se capturó ninguna imagen."
    return render_template('cargar_fotografia.html', mensaje=mensaje)

@app.route('/cargar_documentos', methods=['GET', 'POST'])
def cargar_documentos():
    mensaje = None
    if request.method == 'POST':
        cedula = request.form.get('cedula_documentos')

        # Cargar imagen de la cédula
        if 'cedula_archivo' in request.files and request.files['cedula_archivo'].filename != '':
            cedula_imagen = request.files['cedula_archivo']
            if cedula:
                filename_cedula = f"{cedula}_cedula_archivo.{get_file_extension(cedula_imagen.filename)}"
                filepath_cedula = os.path.join(DATABASE_FOLDER, "cedulas", filename_cedula)
                if not os.path.exists(os.path.join(DATABASE_FOLDER, "cedulas")):
                    os.makedirs(os.path.join(DATABASE_FOLDER, "cedulas"))
                try:
                    cedula_imagen.save(filepath_cedula)
                    mensaje_cedula = f"Imagen de la cédula cargada exitosamente para la cédula: {cedula}."
                    mensaje = mensaje_cedula if mensaje is None else f"{mensaje}<br>{mensaje_cedula}"
                except Exception as e:
                    mensaje_error_cedula = f"Error al guardar la imagen de la cédula: {str(e)}"
                    mensaje = mensaje_error_cedula if mensaje is None else f"{mensaje}<br>{mensaje_error_cedula}"
            else:
                mensaje_error_cedula_no_cedula = "Error: No se proporcionó la cédula para la imagen de la cédula."
                mensaje = mensaje_error_cedula_no_cedula if mensaje is None else f"{mensaje}<br>{mensaje_error_cedula_no_cedula}"

        # Cargar imagen del RIF
        if 'rif_archivo' in request.files and request.files['rif_archivo'].filename != '':
            rif_imagen = request.files['rif_archivo']
            if cedula:
                filename_rif = f"{cedula}_rif_archivo.{get_file_extension(rif_imagen.filename)}"
                filepath_rif = os.path.join(DATABASE_FOLDER, "rifs", filename_rif)
                if not os.path.exists(os.path.join(DATABASE_FOLDER, "rifs")):
                    os.makedirs(os.path.join(DATABASE_FOLDER, "rifs"))
                try:
                    rif_imagen.save(filepath_rif)
                    mensaje_rif = f"Imagen del RIF cargada exitosamente para la cédula: {cedula}."
                    mensaje = mensaje if mensaje is not None else mensaje_rif
                    mensaje = f"{mensaje}<br>{mensaje_rif}" if mensaje_rif else mensaje
                except Exception as e:
                    mensaje_error_rif = f"Error al guardar la imagen del RIF: {str(e)}"
                    mensaje = mensaje if mensaje is not None else mensaje_error_rif
                    mensaje = f"{mensaje}<br>{mensaje_error_rif}" if mensaje_error_rif else mensaje
            else:
                mensaje_error_rif_no_cedula = "Error: No se proporcionó la cédula para la imagen del RIF."
                mensaje = mensaje_error_rif_no_cedula if mensaje is None else f"{mensaje}<br>{mensaje_error_rif_no_cedula}"

        if not mensaje:
            mensaje = "Por favor, seleccione los archivos de la cédula y/o el RIF."

    return render_template('cargar_documentos.html', mensaje=mensaje)

def get_file_extension(filename):
    return filename.rsplit('.', 1)[-1].lower()

@app.route('/generar_curriculum', methods=['GET', 'POST'])
def generar_curriculum():
    mensaje_error = None
    trabajador_data = None
    cedula_buscar = None

    if request.method == 'POST':
        cedula_buscar = request.form.get('cedula_buscar')
        if cedula_buscar:
            filepath = os.path.join(DATABASE_FOLDER, f"{cedula_buscar}.json")
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        trabajador_data = json.load(f)
                    # Generar el PDF
                    pdf_filename = f"{cedula_buscar}_curriculum_archivo.pdf"
                    pdf_filepath = os.path.join(DATABASE_FOLDER, "curriculum", pdf_filename)
                    if not os.path.exists(os.path.join(DATABASE_FOLDER, "curriculum")):
                        os.makedirs(os.path.join(DATABASE_FOLDER, "curriculum"))

                    generate_cv_pdf(trabajador_data, cedula_buscar, pdf_filepath)
                    return send_file(pdf_filepath, as_attachment=True, download_name=pdf_filename)

                except FileNotFoundError:
                    mensaje_error = "El archivo de datos del trabajador no fue encontrado."
                except json.JSONDecodeError:
                    mensaje_error = "Error al decodificar el archivo JSON del trabajador."
                except Exception as e:
                    mensaje_error = f"Error al procesar los datos o generar el PDF: {str(e)}"
            else:
                mensaje_error = "La cédula no pertenece a ningún trabajador."

    return render_template('generar_curriculum.html', mensaje_error=mensaje_error, cedula_buscar=cedula_buscar)

def generate_cv_pdf(data, cedula, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.5 * inch,  # Reducir márgenes para más espacio
                            rightMargin=0.5 * inch,
                            topMargin=0.5 * inch,
                            bottomMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    heading_style = styles['Heading1']
    subheading_style = styles['Heading2']
    detail_style = ParagraphStyle(
        'DetailStyle',
        parent=normal_style,
        leftIndent=20,
        textColor=colors.black
    )

    normal_style.fontSize = 9  # Reducir el tamaño de fuente normal
    detail_style.fontSize = 9  # Reducir el tamaño de fuente de los detalles
    heading_style.fontSize = 13 # Reducir el tamaño de los encabezados principales
    subheading_style.fontSize = 11 # Reducir el tamaño de los subencabezados


    elements = []

    # --- Primera Hoja: Datos del Trabajador ---
    # Agregar la foto si existe
    foto_filename = os.path.join(DATABASE_FOLDER, "fotos", f"{cedula}_foto.png")
    if os.path.exists(foto_filename):
        try:
            img = Image(foto_filename, width=1.5 * inch, height=1.5 * inch)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 0.1 * inch))  # En lugar de 0.2
        except Exception as e:
            print(f"Error al cargar la foto: {e}")

    # Datos Personales
    elements.append(Paragraph(f"{data.get('nombres', '')} {data.get('apellidos', '')}", heading_style))
    elements.append(Paragraph(f"Cédula: {data.get('cedula', '')}", normal_style))
    if data.get('rif'):
        elements.append(Paragraph(f"RIF: {data.get('rif', '')}", normal_style))
    if data.get('fecha_nacimiento'):
        elements.append(Paragraph(f"Fecha de Nacimiento: {data.get('fecha_nacimiento', '')}", normal_style))
    if data.get('lugar_nacimiento'):
        elements.append(Paragraph(f"Lugar de Nacimiento: {data.get('lugar_nacimiento', '')}", normal_style))
    if data.get('edad'):
        elements.append(Paragraph(f"Edad: {data.get('edad', '')}", normal_style))
    if data.get('genero'):
        elements.append(Paragraph(f"Género: {data.get('genero', '')}", normal_style))
    if data.get('estado_civil'):
        elements.append(Paragraph(f"Estado Civil: {data.get('estado_civil', '')}", normal_style))
    if data.get('direccion'):
        elements.append(Paragraph(f"Dirección: {data.get('direccion', '')}", normal_style))
    if data.get('telefono_movil'):
        elements.append(Paragraph(f"Teléfono Móvil: {data.get('telefono_movil', '')}", normal_style))
    if data.get('telefono_local'):
        elements.append(Paragraph(f"Teléfono Local: {data.get('telefono_local', '')}", normal_style))
    if data.get('correo_electronico'):
        elements.append(Paragraph(f"Correo Electrónico: {data.get('correo_electronico', '')}", normal_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Datos de Contacto (Separado por si quieres un encabezado)
    elements.append(Paragraph("Datos de Contacto", subheading_style))
    if data.get('telefono_referencia'):
        elements.append(Paragraph(f"Teléfono de Referencia: {data.get('telefono_referencia', '')}", detail_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Datos Política
    elements.append(Paragraph("Información Política y Social", subheading_style))
    if data.get('org_social'):
        elements.append(Paragraph(f"Organización Social: {data.get('org_social', '')}", detail_style))
    if data.get('voceria'):
        elements.append(Paragraph(f"Vocería: {data.get('voceria', '')}", detail_style))
    if data.get('pertenece_psuv'):
        elements.append(Paragraph(f"Pertenece al PSUV: {data.get('pertenece_psuv', '')}", detail_style))
    if data.get('lugar_vota'):
        elements.append(Paragraph(f"Lugar de Votación: {data.get('lugar_vota', '')}", detail_style))
    if data.get('tiene_emprendimiento'):
        elements.append(Paragraph(f"Tiene Emprendimiento: {data.get('tiene_emprendimiento', '')}", detail_style))
    if data.get('nombre_consejo_comunal'):
        elements.append(Paragraph(f"Consejo Comunal: {data.get('nombre_consejo_comunal', '')}", detail_style))
    if data.get('nombre_comuna'):
        elements.append(Paragraph(f"Comuna: {data.get('nombre_comuna', '')}", detail_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Datos de Salud
    elements.append(Paragraph("Información de Salud", subheading_style))
    if data.get('tipo_sangre'):
        elements.append(Paragraph(f"Tipo de Sangre: {data.get('tipo_sangre', '')}", detail_style))
    if data.get('padece_enfermedad'):
        elements.append(Paragraph(f"Padece Enfermedad: {data.get('padece_enfermedad', '')}", detail_style))
        if data.get('tratamiento'):
            elements.append(Paragraph(f"Tratamiento: {data.get('tratamiento', '')}", detail_style))
    if data.get('discapacidad'):
        elements.append(Paragraph(f"Discapacidad: {data.get('discapacidad', '')}", detail_style))
        if data.get('tipo_discapacidad'):
            elements.append(Paragraph(f"Tipo de Discapacidad: {data.get('tipo_discapacidad', '')}", detail_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Datos Talla del Trabajador
    elements.append(Paragraph("Talla del Trabajador", subheading_style))
    if data.get('talla_zapato'):
        elements.append(Paragraph(f"Talla de Zapato: {data.get('talla_zapato', '')}", detail_style))
    if data.get('talla_camisa'):
        elements.append(Paragraph(f"Talla de Camisa: {data.get('talla_camisa', '')}", detail_style))
    if data.get('talla_pantalon'):
        elements.append(Paragraph(f"Talla de Pantalón: {data.get('talla_pantalon', '')}", detail_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Datos Nomina
    elements.append(Paragraph("Información de Nómina", subheading_style))
    if data.get('tipo_trabajador'):
        elements.append(Paragraph(f"Tipo de Trabajador: {data.get('tipo_trabajador', '')}", detail_style))
    if data.get('fecha_ingreso'):
        elements.append(Paragraph(f"Fecha de Ingreso: {data.get('fecha_ingreso', '')}", detail_style))
    if data.get('cargo'):
        elements.append(Paragraph(f"Cargo: {data.get('cargo', '')}", detail_style))
    if data.get('ubicacion'):
        elements.append(Paragraph(f"Ubicación: {data.get('ubicacion', '')}", detail_style))
    if data.get('departamento'):
        elements.append(Paragraph(f"Departamento: {data.get('departamento', '')}", detail_style))
    if data.get('jefe'):
        elements.append(Paragraph(f"Jefe: {data.get('jefe', '')}", detail_style))
    if data.get('salario_prima'):
        elements.append(Paragraph(f"Salario con Prima: {data.get('salario_prima', '')}", detail_style))
    if data.get('salario_sin_prima'):
        elements.append(Paragraph(f"Salario sin Prima: {data.get('salario_sin_prima', '')}", detail_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Datos Familiares (Cónyuge y Otros)
    elements.append(Paragraph("Información Familiar", subheading_style))
    if data.get('estado_civil') == 'Casado' or data.get('estado_civil') == 'Union':
        if data.get('nombre_conyuge'):
            elements.append(Paragraph(f"Cónyuge: {data.get('nombre_conyuge', '')}", detail_style))
            if data.get('cedula_conyuge'):
                elements.append(Paragraph(f"Cédula del Cónyuge: {data.get('cedula_conyuge', '')}", detail_style))
    if data.get('tiene_familiares') == 'Sí':
        if data.get('nombre_familiar'):
            elements.append(Paragraph(f"Familiar: {data.get('nombre_familiar', '')}", detail_style))
            if data.get('parentesco_familiar'):
                elements.append(Paragraph(f"Parentesco: {data.get('parentesco_familiar', '')}", detail_style))
            if data.get('fecha_nacimiento_familiar'):
                elements.append(Paragraph(f"Fecha de Nacimiento del Familiar: {data.get('fecha_nacimiento_familiar', '')}", detail_style))
                if data.get('edad_familiar'):
                    elements.append(Paragraph(f"Edad del Familiar: {data.get('edad_familiar', '')}", detail_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Datos de los Hijos
    if data.get('hijos'):
        elements.append(Paragraph("Hijos", subheading_style))
        for i, hijo in enumerate(data['hijos']):
            elements.append(Paragraph(f"Hijo(a) {i + 1}:", detail_style))
            if hijo.get('genero'):
                elements.append(Paragraph(f"  Género: {hijo.get('genero', '')}", detail_style))
            if hijo.get('nombres'):
                elements.append(Paragraph(f"  Nombres: {hijo.get('nombres', '')}", detail_style))
            if hijo.get('fecha_nacimiento'):
                elements.append(Paragraph(f"  Fecha de Nacimiento: {hijo.get('fecha_nacimiento', '')}", detail_style))
            if hijo.get('edad'):
                elements.append(Paragraph(f"  Edad: {hijo.get('edad', '')}", detail_style))
            if hijo.get('talla_zapato'):
                elements.append(Paragraph(f"  Talla de Zapato: {hijo.get('talla_zapato', '')}", detail_style))
            if hijo.get('talla_camisa'):
                elements.append(Paragraph(f"  Talla de Camisa: {hijo.get('talla_camisa', '')}", detail_style))
            if hijo.get('talla_pantalon'):
                elements.append(Paragraph(f"  Talla de Pantalón: {hijo.get('talla_pantalon', '')}", detail_style))
            if hijo.get('enfermedad'):
                elements.append(Paragraph(f"  Padece Enfermedad: {hijo.get('enfermedad', '')}", detail_style))
                if hijo.get('tratamiento'):
                    elements.append(Paragraph(f"    Tratamiento: {hijo.get('tratamiento', '')}", detail_style))
            if hijo.get('discapacidad'):
                elements.append(Paragraph(f"  Discapacidad: {hijo.get('discapacidad', '')}", detail_style))
                if hijo.get('tipo_discapacidad'):
                    elements.append(Paragraph(f"    Tipo de Discapacidad: {hijo.get('tipo_discapacidad', '')}", detail_style))
        elements.append(Spacer(1, 0.2 * inch))

    # --- Segunda Hoja: Imágenes de Cédula y RIF (si existen) ---
    cedula_imagen_path = os.path.join(DATABASE_FOLDER, "cedulas")
    rif_imagen_path = os.path.join(DATABASE_FOLDER, "rifs")
    cedula_filename = None
    rif_filename = None

    for filename in os.listdir(cedula_imagen_path) if os.path.exists(cedula_imagen_path) else []:
        if filename.startswith(f"{cedula}_cedula_archivo"):
            cedula_filename = os.path.join(cedula_imagen_path, filename)
            break

    for filename in os.listdir(rif_imagen_path) if os.path.exists(rif_imagen_path) else []:
        if filename.startswith(f"{cedula}_rif_archivo"):
            rif_filename = os.path.join(rif_imagen_path, filename)
            break

    if cedula_filename or rif_filename:
        elements.append(PageBreak())
        elements.append(Paragraph("Documentos", subheading_style))
        elements.append(Spacer(1, 0.2 * inch))

        if cedula_filename:
            try:
                img_cedula = Image(cedula_filename, width=5 * inch, height=3 * inch)
                img_cedula.hAlign = 'CENTER'
                elements.append(Paragraph("Imagen de la Cédula", normal_style))
                elements.append(img_cedula)
                elements.append(Spacer(1, 0.2 * inch))
            except Exception as e:
                print(f"Error al cargar la imagen de la cédula: {e}")

        if rif_filename:
            try:
                img_rif = Image(rif_filename, width=5 * inch, height=3 * inch)
                img_rif.hAlign = 'CENTER'
                elements.append(Paragraph("Imagen del RIF", normal_style))
                elements.append(img_rif)
            except Exception as e:
                print(f"Error al cargar la imagen del RIF: {e}")


@app.route('/reportes_especificos')
def reportes_especificos():
    trabajadores = []
    empleados = 0
    obreros = 0
    jefes_data = defaultdict(lambda: {'empleados': 0, 'obreros': 0, 'trabajadores': []})
    concejos_comunales_data = defaultdict(list)
    psuv_data = []
    centros_votacion_data = defaultdict(list)
    tallas_data = defaultdict(lambda: defaultdict(list))
    carga_familiar_data = []
    trabajadores_con_hijos = []
    trabajadores_con_tratamiento = []
    trabajadores_con_discapacidad = []

    for filename in os.listdir(DATABASE_FOLDER):
        if filename.endswith(".json") and filename != 'usuarios.json':
            filepath = os.path.join(DATABASE_FOLDER, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    trabajador = json.load(f)
                    trabajadores.append(trabajador)
                    tipo_trabajador = trabajador.get('tipo_trabajador', '').lower()
                    if tipo_trabajador == 'empleado':
                        empleados += 1
                    elif tipo_trabajador == 'obrero':
                        obreros += 1

                    jefe = trabajador.get('jefe')
                    if jefe:
                        jefes_data[jefe]['trabajadores'].append(trabajador)
                        if tipo_trabajador == 'empleado':
                            jefes_data[jefe]['empleados'] += 1
                        elif tipo_trabajador == 'obrero':
                            jefes_data[jefe]['obreros'] += 1

                    concejo_comunal = trabajador.get('nombre_consejo_comunal')
                    if concejo_comunal:
                        concejos_comunales_data[concejo_comunal].append(trabajador)

                    if trabajador.get('pertenece_psuv', '').lower() == 'si':
                        psuv_data.append(trabajador)

                    lugar_vota = trabajador.get('lugar_vota')
                    if lugar_vota:
                        centros_votacion_data[lugar_vota].append(trabajador)

                    talla_zapato = trabajador.get('talla_zapato')
                    talla_camisa = trabajador.get('talla_camisa')
                    talla_pantalon = trabajador.get('talla_pantalon')
                    if talla_zapato or talla_camisa or talla_pantalon:
                        tallas_data['zapato'][talla_zapato].append(trabajador)
                        tallas_data['camisa'][talla_camisa].append(trabajador)
                        tallas_data['pantalon'][talla_pantalon].append(trabajador)

                    carga_familiar = len(trabajador.get('hijos', [])) + (1 if trabajador.get('estado_civil', '').lower() in ['casado', 'union'] and trabajador.get('nombre_conyuge') else 0)
                    carga_familiar_data.append({'trabajador': trabajador, 'carga_familiar': carga_familiar})

                    if trabajador.get('hijos'):
                        trabajadores_con_hijos.append(trabajador)

                    if trabajador.get('padece_enfermedad', '').lower() == 'si' and trabajador.get('tratamiento'):
                        trabajadores_con_tratamiento.append(trabajador)

                    if trabajador.get('discapacidad', '').lower() == 'si' and trabajador.get('tipo_discapacidad'):
                        trabajadores_con_discapacidad.append(trabajador)

            except Exception as e:
                print(f"Error al leer archivo {filename}: {e}")

    total_trabajadores = len(trabajadores)
    carga_familiar_data.sort(key=lambda x: x['carga_familiar'], reverse=True)

    return render_template('reportes_especificos.html',
                           total_trabajadores=total_trabajadores,
                           empleados=empleados,
                           obreros=obreros,
                           jefes_data=jefes_data,
                           concejos_comunales_data=concejos_comunales_data,
                           psuv_data=psuv_data,
                           centros_votacion_data=centros_votacion_data,
                           tallas_data=tallas_data,
                           carga_familiar_data=carga_familiar_data,
                           trabajadores_con_hijos=trabajadores_con_hijos,
                           trabajadores_con_tratamiento=trabajadores_con_tratamiento,
                           trabajadores_con_discapacidad=trabajadores_con_discapacidad)

@app.route('/reportes_hijos_por_edad', methods=['POST'])
def reportes_hijos_por_edad():
    edad_min = request.form.get('edad_min')
    edad_max = request.form.get('edad_max')
    trabajadores_filtrados = []
    # Implementar la lógica para filtrar trabajadores por rango de edad de sus hijos
    return render_template('reporte_hijos_por_edad.html', trabajadores=trabajadores_filtrados, edad_min=edad_min, edad_max=edad_max)

@app.route('/reportes_personalizado', methods=['GET', 'POST'])
def reportes_personalizado():
    if request.method == 'POST':
        # Implementar la lógica para el filtro personalizado
        filtros = request.form  # Aquí tendrás los criterios de filtro
        resultados = []
        # Filtrar la lista de trabajadores basados en 'filtros'
        return render_template('reporte_personalizado_resultados.html', resultados=resultados, filtros=filtros)
    return render_template('reporte_personalizado_form.html')

def generar_contenido_reporte_seccion(data, seccion):
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    heading_style = styles['Heading1']
    subheading_style = styles['Heading2']
    h3_style = styles['h3']
    h4_style = styles['h4']
    h5_style = styles['h5']

    contenido = []
    contenido.append(Paragraph(f"Reporte Específico - {seccion.replace('_', ' ').title()}", heading_style))
    contenido.append(Spacer(1, 0.2 * inch))

    if seccion == 'generales':
        contenido.append(Paragraph("Generales", subheading_style))
        contenido.append(Paragraph(f"Cantidad total de trabajadores: {data['total_trabajadores']}", normal_style))
        contenido.append(Paragraph(f"Cantidad de empleados: {data['empleados']}", normal_style))
        contenido.append(Paragraph(f"Cantidad de obreros: {data['obreros']}", normal_style))
    elif seccion == 'jefes':
        contenido.append(Paragraph("Lista de trabajadores por Jefes", subheading_style))
        for jefe, jefe_data in data['jefes_data'].items():
            contenido.append(Paragraph(f"<b>{jefe}</b>", h3_style))
            contenido.append(Paragraph(f"Total a cargo: {jefe_data['empleados'] + jefe_data['obreros']} (Empleados: {jefe_data['empleados']}, Obreros: {jefe_data['obreros']})", normal_style))
            table_data = [['Nombre', 'Cédula', 'Teléfono']]
            for trabajador in jefe_data['trabajadores']:
                table_data.append([f"{trabajador.get('nombres', '')} {trabajador.get('apellidos', '')}", trabajador.get('cedula', ''), trabajador.get('telefono_movil', '')])
            table = Table(table_data)
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                       ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                       ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                       ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                       ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                       ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                       ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
            contenido.append(table)
            contenido.append(Spacer(1, 0.1 * inch))
    elif seccion == 'concejos':
        contenido.append(Paragraph("Lista de trabajadores por Concejos Comunales", subheading_style))
        for concejo, trabajadores in data['concejos_comunales_data'].items():
            contenido.append(Paragraph(f"<b>{concejo}</b>", h3_style))
            table_data = [['Nombre', 'Cédula', 'Teléfono']]
            for trabajador in trabajadores:
                table_data.append([f"{trabajador.get('nombres', '')} {trabajador.get('apellidos', '')}", trabajador.get('cedula', ''), trabajador.get('telefono_movil', '')])
            table = Table(table_data)
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                       ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                       ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                       ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                       ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                       ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                       ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
            contenido.append(table)
            contenido.append(Spacer(1, 0.1 * inch))
    elif seccion == 'psuv':
        contenido.append(Paragraph("Lista de trabajadores pertenecientes al PSUV", subheading_style))
        table_data = [['Nombre', 'Cédula', 'Teléfono']]
        for trabajador in data['psuv_data']:
            table_data.append([f"{trabajador.get('nombres', '')} {trabajador.get('apellidos', '')}", trabajador.get('cedula', ''), trabajador.get('telefono_movil', '')])
        table = Table(table_data)
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                   ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                   ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                   ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                   ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                   ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                   ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        contenido.append(table)
    elif seccion == 'centros':
        contenido.append(Paragraph("Lista de trabajadores por Centro de Votación", subheading_style))
        for centro, trabajadores in data['centros_votacion_data'].items():
            contenido.append(Paragraph(f"<b>{centro}</b>", h3_style))
            table_data = [['Nombre', 'Cédula', 'Teléfono', 'Dirección']]
            for trabajador in trabajadores:
                table_data.append([f"{trabajador.get('nombres', '')} {trabajador.get('apellidos', '')}", trabajador.get('cedula', ''), trabajador.get('telefono_movil', ''), trabajador.get('direccion', '')])
            table = Table(table_data)
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                       ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                       ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                       ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                       ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                       ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                       ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
            contenido.append(table)
            contenido.append(Spacer(1, 0.1 * inch))
    elif seccion == 'tallas':
        contenido.append(Paragraph("Lista de trabajadores por tallas de Camisa, Pantalón y calzado", subheading_style))
        for tipo_talla, tallas in data['tallas_data'].items():
            contenido.append(Paragraph(f"<b>Tallas de {tipo_talla.capitalize()}</b>", h4_style))
            for talla, trabajadores in tallas.items():
                if talla:
                    contenido.append(Paragraph(f"<b>Talla: {talla}</b>", h5_style))
                    lista_trabajadores = [f"- {trabajador.get('nombres', '')} {trabajador.get('apellidos', '')}" for trabajador in trabajadores]
                    contenido.append(Paragraph("<br/>".join(lista_trabajadores), normal_style))
            contenido.append(Spacer(1, 0.1 * inch))
    elif seccion == 'carga_familiar':
        contenido.append(Paragraph("Lista de trabajadores por numero de Carga Familiar (Mayor a Menor)", subheading_style))
        table_data = [['Nombre', 'Cédula', 'Teléfono', 'Carga Familiar']]
        for item in data['carga_familiar_data']:
            trabajador = item['trabajador']
            table_data.append([f"{trabajador.get('nombres', '')} {trabajador.get('apellidos', '')}", trabajador.get('cedula', ''), trabajador.get('telefono_movil', ''), str(item['carga_familiar'])])
        table = Table(table_data)
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                   ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                   ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                   ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                   ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                   ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                   ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        contenido.append(table)
    elif seccion == 'hijos':
        contenido.append(Paragraph("Lista de trabajadores con hijos e hijas", subheading_style))
        for trabajador in data['trabajadores_con_hijos']:
            contenido.append(Paragraph(f"<b>{trabajador.get('nombres', '')} {trabajador.get('apellidos', '')}</b> - Cédula: {trabajador.get('cedula', '')} - Teléfono: {trabajador.get('telefono_movil', '')} - Hijos: {len(trabajador.get('hijos', []))}", normal_style))
            for hijo in trabajador.get('hijos', []):
                contenido.append(Paragraph(f"- {hijo.get('genero', 'No especificado')} - {hijo.get('nombres', 'Sin nombre')} (Edad: {hijo.get('edad', 'Desconocida')}, Zapato: {hijo.get('talla_zapato', 'N/A')}, Camisa: {hijo.get('talla_camisa', 'N/A')}, Pantalón: {hijo.get('talla_pantalon', 'N/A')})", normal_style))
            contenido.append(Spacer(1, 0.1 * inch))
    elif seccion == 'tratamiento':
        contenido.append(Paragraph("Lista de trabajadores con tratamiento", subheading_style))
        table_data = [['Nombre', 'Cédula', 'Teléfono', 'Tratamiento', 'Enfermedad']]
        for trabajador in data['trabajadores_con_tratamiento']:
            table_data.append([f"{trabajador.get('nombres', '')} {trabajador.get('apellidos', '')}", trabajador.get('cedula', ''), trabajador.get('telefono_movil', ''), trabajador.get('tratamiento', ''), trabajador.get('padece_enfermedad', '')])
        table = Table(table_data)
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                   ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                   ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                   ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                   ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                   ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                   ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        contenido.append(table)
    elif seccion == 'discapacidad':
        contenido.append(Paragraph("Lista de trabajadores con discapacidad", subheading_style))
        table_data = [['Nombre', 'Cédula', 'Teléfono', 'Tipo de Discapacidad']]
        for trabajador in data['trabajadores_con_discapacidad']:
            table_data.append([f"{trabajador.get('nombres', '')} {trabajador.get('apellidos', '')}", trabajador.get('cedula', ''), trabajador.get('telefono_movil', ''), trabajador.get('tipo_discapacidad', '')])
        table = Table(table_data)
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                   ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                   ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                   ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                   ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                   ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                   ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        contenido.append(table)

    return contenido

@app.route('/guardar_reporte_especifico_seccion/<seccion>')
def guardar_reporte_especifico_seccion(seccion):
    data_reporte = obtener_data_reportes()
    contenido_reporte = generar_contenido_reporte_seccion(data_reporte, seccion)
    texto_reporte = ""
    for item in contenido_reporte:
        if isinstance(item, Paragraph):
            texto_reporte += item.getPlainText() + "\n"
        elif isinstance(item, Table):
            for row in item._data:
                texto_reporte += "\t".join(row) + "\n"
        elif isinstance(item, Spacer):
            texto_reporte += "\n"

    filename = f"reporte_{seccion}.txt"
    filepath = os.path.join(app.root_path, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(texto_reporte)
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/generar_pdf_reporte_especifico_seccion/<seccion>')
def generar_pdf_reporte_especifico_seccion(seccion):
    data_reporte = obtener_data_reportes()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    contenido = generar_contenido_reporte_seccion(data_reporte, seccion)
    doc.build(contenido)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"reporte_{seccion}.pdf", mimetype='application/pdf')

   
if __name__ == '__main__':
    app.run(debug=True)