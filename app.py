# ======== IMPORTACIONES ========
import os
from flask import render_template, request, redirect, url_for, flash, get_flashed_messages
from conexion import app, db
from models import Respuesta, Politico, Pregunta, Proyecto
from sqlalchemy import func
from sqlalchemy.orm import joinedload

app.secret_key = os.getenv('SECRET_KEY', 'dev-secret')

# ======== RUTAS BÁSICAS ========
@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

# ======== ENCUESTA ========
@app.route('/encuesta')
@app.route('/encuesta/<int:id_politico>', methods=['GET', 'POST'])
def encuesta(id_politico=None):
    if id_politico is None:
        p_first = Politico.query.first()
        if not p_first:
            return '<h2>No hay políticos cargados</h2>', 404
        return redirect(url_for('encuesta', id_politico=p_first.id))

    politico = Politico.query.get_or_404(id_politico)

    if request.method == 'POST':
        for i in range(1, 8):
            opinion_valor = request.form.get(f'preg{i}')
            if not opinion_valor:
                continue
            db.session.add(Respuesta(
                id_politico=id_politico,
                id_pregunta=i,
                id_opinion=int(opinion_valor)
            ))
        db.session.commit()
        flash('Encuesta guardada correctamente.')
        redirect_url = request.form.get('redirect_url') or url_for('mostrar_encuesta')
        return redirect(redirect_url)

    if Pregunta.query.count() == 0:
        for t in [
            "¿Cumple con sus promesas?",
            "¿Nivel de transparencia?",
            "¿Usa correctamente los recursos?",
            "¿Volverías a votarlo?",
            "¿Compromiso con el bienestar ciudadano?",
            "¿Rinde cuentas ante la ciudadanía?",
            "¿Palabra que lo describe mejor?"
        ]:
            db.session.add(Pregunta(descripcion=t))
        db.session.commit()

    preguntas = Pregunta.query.all()
    mensajes = get_flashed_messages()
    return render_template('encuesta.html', p=politico, preguntas=preguntas, mensajes=mensajes)

# ======== RESULTADOS ========
@app.route('/resultados/<int:id_politico>')
def resultados_por_politico(id_politico):
    politico = Politico.query.get_or_404(id_politico)
    preguntas = Pregunta.query.all()
    data = []

    for pregunta in preguntas:
        opciones = {1: 0, 2: 0, 3: 0, 4: 0}
        conteos = (
            db.session.query(Respuesta.id_opinion, func.count(Respuesta.id_respuesta))
            .filter(
                Respuesta.id_pregunta == pregunta.id_pregunta,
                Respuesta.id_politico == id_politico
            )
            .group_by(Respuesta.id_opinion)
            .all()
        )
        for opinion, cantidad in conteos:
            opciones[opinion] = cantidad

        labels = [f"Opción {k}" for k in opciones.keys()]
        valores = list(opciones.values())

        data.append({
            "pregunta": pregunta.descripcion,
            "labels": labels,
            "valores": valores
        })

    return render_template('resultados.html', resultados=data, politico=politico)

# ======== CARGA INICIAL ========
def cargar_politicos_si_no_existen():
    datos = [
        # ... (tu bloque de datos se mantiene igual, lo omito por brevedad)
        # NO CAMBIÉ NADA aquí
    ]
    for d in datos:
        existente = Politico.query.filter_by(nombre=d["nombre"]).first()
        if not existente:
            nuevo = Politico(
                nombre=d["nombre"],
                partido=d["partido"],
                titulo=d["titulo"],
                foto=d["foto"]
            )
            db.session.add(nuevo)
            db.session.commit()
            for p in d["proyectos"]:
                db.session.add(Proyecto(
                    id_politico=nuevo.id,
                    titulo=p["titulo"],
                    descripcion=p["descripcion"]
                ))
    db.session.commit()

# ======== FILTROS ========
@app.route("/mostrarencuesta")
def mostrar_encuesta():
    politicos = Politico.query.options(joinedload(Politico.proyectos)).all()
    proyectos = Proyecto.query.all()
    if not politicos:
        return '<h2>No hay políticos cargados</h2>', 404
    return render_template('politicos.html', politicos=politicos, proyectos=proyectos)

@app.route("/presidentes")
def mostrar_presidentes():
    presidentes = (
        Politico.query.options(joinedload(Politico.proyectos))
        .filter(Politico.titulo.ilike("%presidente%"))
        .all()
    )
    if not presidentes:
        return '<h2>No hay presidentes cargados</h2>', 404
    return render_template('politicos.html', politicos=presidentes)

@app.route("/diputados")
def mostrar_diputados():
    diputados = (
        Politico.query.options(joinedload(Politico.proyectos))
        .filter(Politico.titulo.ilike("%diputado%"))
        .all()
    )
    if not diputados:
        return '<h2>No hay diputados cargados</h2>', 404
    return render_template('politicos.html', politicos=diputados)

@app.route("/senadores")
def mostrar_senadores():
    senadores = (
        Politico.query.options(joinedload(Politico.proyectos))
        .filter(Politico.titulo.ilike("%senador%"))
        .all()
    )
    if not senadores:
        return '<h2>No hay senadores cargados</h2>', 404
    return render_template('politicos.html', politicos=senadores)

# === RUTA TEMPORAL PARA SEMBRAR DATOS ===
from models import Politico, db

@app.route("/seed")
def seed():
    db.create_all()  # crea las tablas si no existen

    if not Politico.query.first():
        db.session.add(Politico(nombre="Santiago Peña", cargo="Presidente"))
        db.session.add(Politico(nombre="Pedro Alliana", cargo="Vicepresidente"))
        db.session.add(Politico(nombre="Celeste Amarilla", cargo="Diputada"))
        db.session.add(Politico(nombre="Esperanza Martínez", cargo="Senadora"))
        db.session.commit()
        return "Seed ejecutado ✅"
    else:
        return "Ya existen datos 🌱"


# ======== EJECUCIÓN PRINCIPAL ========
if __name__ == '__main__':
    with app.app_context():
        cargar_politicos_si_no_existen()
    app.run(debug=True)
