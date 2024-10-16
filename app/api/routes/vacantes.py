import json
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import tuple_
from sqlalchemy.sql.functions import grouping_sets
from sqlmodel import distinct, func, or_, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    CatalogoCeco,
    CatalogoFuncion,
    CatalogoPosicion,
    DireccionIngreso,
    EfectividadReclutador,
    FuncionIngreso,
    GrupoIngreso,
    Ingreso,
    Ingresos,
    JerarquiaIngreso,
    Message,
    MiEfectividad,
    MotivoIngreso,
    ReclutadorEstatusIngreso,
    ReclutadorIngreso,
    User,
    Vacante,
    VacanteCreate,
    VacanteHistory,
    VacantePublic,
    VacanteReinicio,
    VacantesHistory,
    VacantesPublic,
    VacantesReinicio,
    VacanteUpdate,
    VacanteUpdateReinicio,
    VacanteUpdateRys,
)

CATALOGO_UBICACIONES = {
    "0691": "OFICINAS UVL",
    "0805": "OFICINA SHANGHAI",
    "0487": "OFICINAS MARIO PANI",
    "0900": "COMISARIATO",
    "0395": "OFICINAS QUAD",
    "0694": "OFICINAS LIVERPOOL SANTA FE",
}

router = APIRouter()

logging.basicConfig(level=logging.INFO)


@router.get("/", response_model=VacantesPublic)
def read_vacantes(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    dir_corp: str | None = Query(None),
    filters: str | None = Query(None),  # Add a filters parameter to accept JSON filters
    searchQuery: str | None = Query(None),
) -> Any:
    """
    Retrieve vacantes.
    """
    statement = select(Vacante)
    if dir_corp:
        dir_corp_list = json.loads(dir_corp)
        if len(dir_corp_list) > 0:
            statement = statement.where(Vacante.dir_corp.in_(dir_corp_list))

    if filters:
        filters_dict = json.loads(filters)

        for key, values in filters_dict.items():
            if values:
                if key != "dir_corp" and key != "searchQuery":
                    statement = statement.where(getattr(Vacante, key).in_(values))
                    # Check if the key is 'anio' or 'mes' and convert values to integers
                    if key in ["anio", "mes"]:
                        values = [int(value) for value in values]
                    statement = statement.where(getattr(Vacante, key).in_(values))

    if searchQuery:
        term = searchQuery.replace('"', "").replace("'", "")
        search_conditions = []
        # Filter columns to include only string type columns
        string_columns = [
            attr.key
            for attr in Vacante.__table__.columns
            if str(attr.type) == "VARCHAR"
        ]
        condition = or_(
            *(getattr(Vacante, attr).ilike(f"%{term}%") for attr in string_columns)
        )
        search_conditions.append(condition)
        if search_conditions:
            statement = statement.where(or_(*search_conditions))

    count_statement = select(func.count()).select_from(statement)
    count = session.exec(count_statement).one()

    statement = statement.order_by(Vacante.fecha.desc()).offset(skip).limit(limit)
    vacantes = session.exec(statement).all()

    return VacantesPublic(data=vacantes, count=count)


@router.get("/all", response_model=VacantesPublic)
def read_all_vacantes(
    session: SessionDep,
    dir_corp: str | None = Query(None),
    filters: str | None = Query(None),  # Add a filters parameter to accept JSON filters
    searchQuery: str | None = Query(None),
) -> Any:
    """
    Retrieve vacantes.
    """
    statement = select(Vacante)
    if dir_corp:
        dir_corp_list = json.loads(dir_corp)
        if len(dir_corp_list) > 0:
            statement = statement.where(Vacante.dir_corp.in_(dir_corp_list))

    if filters:
        filters_dict = json.loads(filters)

        for key, values in filters_dict.items():
            if values:
                if key != "dir_corp" and key != "searchQuery":
                    statement = statement.where(getattr(Vacante, key).in_(values))
                    # Check if the key is 'anio' or 'mes' and convert values to integers
                    if key in ["anio", "mes"]:
                        values = [int(value) for value in values]
                    statement = statement.where(getattr(Vacante, key).in_(values))

    if searchQuery:
        term = searchQuery.replace('"', "").replace("'", "")
        search_conditions = []
        # Filter columns to include only string type columns
        string_columns = [
            attr.key
            for attr in Vacante.__table__.columns
            if str(attr.type) == "VARCHAR"
        ]
        condition = or_(
            *(getattr(Vacante, attr).ilike(f"%{term}%") for attr in string_columns)
        )
        search_conditions.append(condition)
        if search_conditions:
            statement = statement.where(or_(*search_conditions))

    count_statement = select(func.count()).select_from(statement)
    count = session.exec(count_statement).one()

    statement = statement.order_by(Vacante.fecha.desc(), Vacante.id_pos.desc())
    vacantes = session.exec(statement).all()

    return VacantesPublic(data=vacantes, count=count)


@router.get("/dashboard", response_model=VacantesPublic)
def read_vacantes_dashboard(
    session: SessionDep,
    filters: str | None = Query(None),  # Add a filters parameter to accept JSON filters
) -> Any:
    """
    Retrieve vacantes.
    """

    statement = select(Vacante)
    if filters:
        filters_dict = json.loads(filters)

        for key, values in filters_dict.items():
            if values:
                if key in ["anio", "mes"]:
                    values = [int(value["value"]) for value in values]
                statement = statement.where(getattr(Vacante, key).in_(values))

    count_statement = select(func.count()).select_from(statement)
    count = session.exec(count_statement).one()

    statement = statement.order_by(Vacante.fecha.desc(), Vacante.id_pos.desc())
    vacantes = session.exec(statement).all()

    return VacantesPublic(data=vacantes, count=count)


@router.get("/ingresos", response_model=Ingresos)
def read_ingresos_dashboard(
    session: SessionDep,
    filters: str | None = Query(None),  # Add a filters parameter to accept JSON filters
) -> Any:
    """
    Retrieve ingresos.
    """

    statement = select(Ingreso)

    if filters:
        filters_dict = json.loads(filters)

        for key, values in filters_dict.items():
            if values:
                if key in ["anio", "mes"]:
                    values = [int(value["value"]) for value in values]
                statement = statement.where(getattr(Ingreso, key).in_(values))

    count_statement = select(func.count()).select_from(statement)
    count = session.exec(count_statement).one()

    statement = statement.order_by(Ingreso.anio.desc(), Ingreso.mes.desc(), Ingreso.id_pos.desc())
    ingresos = session.exec(statement).all()

    return Ingresos(data=ingresos, count=count)


@router.get("/efectividad", response_model=EfectividadReclutador)
def read_efectividad_dashboard(
    session: SessionDep,
    filters: str | None = Query(None),  # Add a filters parameter to accept JSON filters
) -> Any:
    """
    Retrieve ingresos.
    """

    statement = select(Ingreso)

    if filters:
        filters_dict = json.loads(filters)
        for key, values in filters_dict.items():
            if values:
                if key in ["anio", "mes"]:
                    values = [int(value["value"]) for value in values]
                statement = statement.where(getattr(Ingreso, key).in_(values))


    # Create a CTE for the filtered data
    cte = statement.cte("filtered_data")

    aggregated_data = session.exec(
        select(cte.c.id_fun,
            cte.c.deno_fun,
            cte.c.jefe_inmediato,
            cte.c.dir_corp,
            cte.c.gpo_per,
             cte.c.jerarquia,
             cte.c.id_reclutador,
            cte.c.nombre_reclutador,
            cte.c.motivo,
            cte.c.estatus,
            func.sum(func.IF(cte.c.estatus == "Baja", 1, 0)).label('bajas'),
        func.round(func.avg(func.IF(cte.c.estatus == "Baja", cte.c.tiempo_cobertura, None)),0).label('tiempo_cobertura'),
        func.round(func.avg(func.IF(cte.c.estatus == "Baja", cte.c.meses_activo, None)),0).label('meses_activo'),
        func.count(cte.c.num_per).label('ingresos'),
        func.round(func.avg(cte.c.meses_activo),0).label('meses_activo_ingresos')

               ).group_by(
                   grouping_sets(
                       tuple_(cte.c.id_fun, cte.c.deno_fun, cte.c.jefe_inmediato),
                       cte.c.dir_corp,
                          cte.c.gpo_per,
                            cte.c.jerarquia,
                            tuple_(cte.c.id_reclutador, cte.c.nombre_reclutador),
                            cte.c.motivo,
                            tuple_(cte.c.id_reclutador, cte.c.nombre_reclutador, cte.c.estatus)
                   )).order_by(cte.c.id_fun, cte.c.jefe_inmediato, cte.c.dir_corp, cte.c.gpo_per, cte.c.jerarquia,  cte.c.motivo, cte.c.nombre_reclutador, cte.c.estatus)).all()
    
    funcion_ingreso = [
        FuncionIngreso(
            id_fun=row.id_fun,
            deno_fun=row.deno_fun,
            jefe_inmediato=row.jefe_inmediato,
            bajas=row.bajas,
        )
        for row in aggregated_data
        if row.id_fun and row.jefe_inmediato
    ]

    direccion_ingreso = [
        DireccionIngreso(
            dir_corp=row.dir_corp,
            bajas=row.bajas,
            tiempo_cobertura=row.tiempo_cobertura,
            meses_activo=row.meses_activo,
        )
        for row in aggregated_data
        if row.dir_corp
    ]

    grupo_ingreso = [
        GrupoIngreso(
            gpo_per=row.gpo_per,
            bajas=row.bajas,
            tiempo_cobertura=row.tiempo_cobertura,
        )
        for row in aggregated_data
        if row.gpo_per
    ]

    jerarquia_ingreso = [
        JerarquiaIngreso(
            jerarquia=row.jerarquia,
            bajas=row.bajas,
            tiempo_cobertura=row.tiempo_cobertura,
        )
        for row in aggregated_data
        if row.jerarquia
    ]

    reclutador_ingreso = [
        ReclutadorIngreso(
            nombre_reclutador=row.nombre_reclutador,
            bajas=row.bajas,
            tiempo_cobertura=row.tiempo_cobertura,
        )
        for row in aggregated_data
        if row.id_reclutador and not row.estatus
    ]

    motivo_ingreso = [
        MotivoIngreso(
            motivo=row.motivo,
            bajas=row.bajas,
            meses_activo=row.meses_activo,
        )
        for row in aggregated_data
        if row.motivo
    ]

    reclutador_estatus_ingreso = [
        ReclutadorEstatusIngreso(
            nombre_reclutador=row.nombre_reclutador,
            estatus=row.estatus,
            ingresos=row.ingresos,
            meses_activo=row.meses_activo_ingresos,
        )
        for row in aggregated_data
        if row.id_reclutador and row.estatus
    ]

    return EfectividadReclutador(
        funcion_ingreso=funcion_ingreso,
        direccion_ingreso=direccion_ingreso,
        grupo_ingreso=grupo_ingreso,
        jerarquia_ingreso=jerarquia_ingreso,
        motivo_ingreso=motivo_ingreso,
        reclutador_ingreso=reclutador_ingreso,
        reclutador_estatus_ingreso=reclutador_estatus_ingreso,
    )


@router.get("/mi_efectividad", response_model=MiEfectividad)
def read_mi_efectividad_dashboard(
    session: SessionDep,
    current_user: CurrentUser,
    filters: str | None = Query(None),  # Add a filters parameter to accept JSON filters
) -> Any:
    """
    Retrieve mis ingresos.
    """

    current_user_id = current_user.id

    statement = select(Ingreso).where(Ingreso.id_reclutador == current_user_id)

    if filters:
        filters_dict = json.loads(filters)
        for key, values in filters_dict.items():
            if values:
                if key in ["anio", "mes"]:
                    values = [int(value["value"]) for value in values]
                statement = statement.where(getattr(Ingreso, key).in_(values))

    statement = statement.order_by(Ingreso.anio.desc(), Ingreso.mes.desc())

     # Create a CTE for the filtered data
    cte = statement.cte("filtered_data")

    aggregated_data = session.exec(
        select(cte.c.id_fun,
            cte.c.deno_fun,
            cte.c.jefe_inmediato,
            cte.c.dir_corp,
            cte.c.gpo_per,
             cte.c.jerarquia,
             cte.c.id_reclutador,
            cte.c.nombre_reclutador,
            cte.c.motivo,
            cte.c.estatus,
            func.sum(func.IF(cte.c.estatus == "Baja", 1, 0)).label('bajas'),
        func.round(func.avg(func.IF(cte.c.estatus == "Baja", cte.c.tiempo_cobertura, None)),0).label('tiempo_cobertura'),
        func.round(func.avg(func.IF(cte.c.estatus == "Baja", cte.c.meses_activo, None)),0).label('meses_activo'),
        func.count(cte.c.num_per).label('ingresos'),
        func.round(func.avg(cte.c.meses_activo),0).label('meses_activo_ingresos')

               ).group_by(
                   grouping_sets(
                       tuple_(cte.c.id_fun, cte.c.deno_fun, cte.c.jefe_inmediato),
                       cte.c.dir_corp,
                          cte.c.gpo_per,
                            cte.c.jerarquia,
                            tuple_(cte.c.id_reclutador, cte.c.nombre_reclutador),
                            cte.c.motivo,
                            tuple_(cte.c.id_reclutador, cte.c.nombre_reclutador, cte.c.estatus)
                   )).order_by(cte.c.id_fun, cte.c.jefe_inmediato, cte.c.dir_corp, cte.c.gpo_per, cte.c.jerarquia,  cte.c.motivo, cte.c.nombre_reclutador, cte.c.estatus)).all()
    
    funcion_ingreso = [
        FuncionIngreso(
            id_fun=row.id_fun,
            deno_fun=row.deno_fun,
            jefe_inmediato=row.jefe_inmediato,
            bajas=row.bajas,
        )
        for row in aggregated_data
        if row.id_fun and row.jefe_inmediato
    ]

    direccion_ingreso = [
        DireccionIngreso(
            dir_corp=row.dir_corp,
            bajas=row.bajas,
            tiempo_cobertura=row.tiempo_cobertura,
            meses_activo=row.meses_activo,
        )
        for row in aggregated_data
        if row.dir_corp
    ]

    grupo_ingreso = [
        GrupoIngreso(
            gpo_per=row.gpo_per,
            bajas=row.bajas,
            tiempo_cobertura=row.tiempo_cobertura,
        )
        for row in aggregated_data
        if row.gpo_per
    ]

    jerarquia_ingreso = [
        JerarquiaIngreso(
            jerarquia=row.jerarquia,
            bajas=row.bajas,
            tiempo_cobertura=row.tiempo_cobertura,
        )
        for row in aggregated_data
        if row.jerarquia
    ]

    reclutador_ingreso = [
        ReclutadorIngreso(
            nombre_reclutador=row.nombre_reclutador,
            bajas=row.bajas,
            tiempo_cobertura=row.tiempo_cobertura,
        )
        for row in aggregated_data
        if row.id_reclutador and not row.estatus
    ]

    if len(reclutador_ingreso) > 0:
        reclutador_ingreso = reclutador_ingreso[0]
    else:
        reclutador_ingreso = None

    motivo_ingreso = [
        MotivoIngreso(
            motivo=row.motivo,
            bajas=row.bajas,
            meses_activo=row.meses_activo,
        )
        for row in aggregated_data
        if row.motivo
    ]

    reclutador_estatus_ingreso = [
        ReclutadorEstatusIngreso(
            nombre_reclutador=row.nombre_reclutador,
            estatus=row.estatus,
            ingresos=row.ingresos,
            meses_activo=row.meses_activo_ingresos,
        )
        for row in aggregated_data
        if row.id_reclutador and row.estatus
    ]
    

    if len(reclutador_estatus_ingreso) > 0:
        reclutador_estatus_ingreso = reclutador_estatus_ingreso[0]
    else:
        reclutador_estatus_ingreso = None

    return MiEfectividad(
        funcion_ingreso=funcion_ingreso,
        direccion_ingreso=direccion_ingreso,
        grupo_ingreso=grupo_ingreso,
        jerarquia_ingreso=jerarquia_ingreso,
        motivo_ingreso=motivo_ingreso,
        reclutador_ingreso=reclutador_ingreso,
        reclutador_estatus_ingreso=reclutador_estatus_ingreso,
    )


@router.get("/reinicio", response_model=VacantesReinicio)
def read_vacantes_reinicio(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve reinicio vacantes.
    """

    count_statement = select(func.count()).select_from(VacanteReinicio)
    count = session.exec(count_statement).one()
    statement = select(VacanteReinicio).order_by(VacanteReinicio.fecha.desc())
    vacantes = session.exec(statement).all()

    return VacantesReinicio(data=vacantes, count=count)

@router.get("/historico", response_model=VacantesHistory)
def read_vacantes_historico(
    session: SessionDep
) -> Any:
    """
    Retrieve historico vacantes.
    """
    count_statement = select(func.count()).select_from(VacanteHistory)
    count = session.exec(count_statement).one()
    statement = select(VacanteHistory).order_by(VacanteHistory.fecha.desc())
    vacantes = session.exec(statement).all()
    return VacantesHistory(data=vacantes, count=count)

@router.get("/historico/{id}", response_model=VacantesHistory)
def read_vacante_historico(
    session: SessionDep,  id: str
) -> Any:
    """
    Retrieve historico vacantes by ID vacante.
    """

    count_statement = select(func.count()).select_from(VacanteHistory).where(VacanteHistory.id_vacante == id)
    count = session.exec(count_statement).one()
    statement = select(VacanteHistory).where(VacanteHistory.id_vacante==id).order_by(VacanteHistory.fecha.asc())
    vacantes = session.exec(statement).all()

    return VacantesHistory(data=vacantes, count=count)

@router.get("/filter-options", response_model=Any)
def read_filter_options(session: SessionDep, columns: str | None = Query(None)) -> Any:
    """
    Get unique filter options for each column.
    """
    filter_options = {}

    if columns:
        columns = json.loads(columns)
        for column in columns:
            statement = select(distinct(getattr(Vacante, column))).order_by(
                getattr(Vacante, column)
            )

            result = session.exec(statement).all()
            filter_options[column] = result

    return filter_options


@router.get("/{id}", response_model=VacantePublic)
def read_vacante(session: SessionDep, id: str) -> Any:
    """
    Get vacante by ID.
    """
    vacante = session.get(Vacante, id)

    if not vacante:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")
    # if not current_user.is_superuser and (vacante.id_bp != current_user.id):
    #     raise HTTPException(status_code=400, detail="Sin suficientes permisos")
    return vacante


@router.post("/", response_model=VacantePublic)
def create_vacante(
    *, session: SessionDep, current_user: CurrentUser, vacante_in: VacanteCreate
) -> Any:
    """
    Create new vacante.
    """

    # Initialize default values
    pos, fun, nivel1, nivel2, nivel3, reclutador = None, None, None, None, None, None

    # get deno_pos and deno_fun
    try:
        pos = session.get(CatalogoPosicion, vacante_in.id_pos).deno_pos
    except (
        AttributeError
    ):  # Replace SomeSpecificException with the actual exception type
        pos = "Posición no encontrada"
        # insert the position in the db CatalogoPosicion table
        new_pos = CatalogoPosicion(id_pos=vacante_in.id_pos, deno_pos=pos)
        session.add(new_pos)
        session.commit()

    if vacante_in.id_fun:
        try:
            fun = session.get(CatalogoFuncion, vacante_in.id_fun).deno_fun
        except (
            AttributeError
        ):  # Replace SomeSpecificException with the actual exception type
            fun = "Función no encontrada"

    if vacante_in.id_ceco:
        try:
            ceco = session.get(CatalogoCeco, vacante_in.id_ceco)
            nivel1 = ceco.nivel1
            nivel2 = ceco.nivel2
            nivel3 = ceco.nivel3
        except AttributeError:
            nivel1 = "CECO no encontrado"
            nivel2 = "CECO no encontrado"
            nivel3 = "CECO no encontrado"

    # make sure the sueldos are integers
    # if vacante_in.sueldo_via_planta_76:
    #     vacante_in.sueldo_via_planta_76 = int(vacante_in.sueldo_via_planta_76)

    # if vacante_in.sueldo_planta_80:
    #     vacante_in.sueldo_planta_80 = int(vacante_in.sueldo_planta_80)

    if vacante_in.ubi_ceco:
        # map txt_ubi ceco with CATALOGO_UBICACIONES
        vacante_in.txt_ubi_ceco = CATALOGO_UBICACIONES.get(
            vacante_in.ubi_ceco, "Ubicación no encontrada"
        )

    vacante = Vacante.model_validate(
        vacante_in,
        update={
            "id_bp": current_user.id,
            "nombre_bp": current_user.full_name,
            "email_bp": current_user.email,
            "id": uuid4().hex,
            "deno_fun": fun,
            "deno_pos": pos,
            "nivel1": nivel1,
            "nivel2": nivel2,
            "nivel3": nivel3,
            "rys_is_tracked": True,
        },
    )
    # Create a new history record for the vacante
    vacante_history = VacanteHistory(
        id=uuid4().hex,
        id_vacante=vacante.id,
        id_bp=vacante.id_bp,
        nombre_bp=vacante.nombre_bp,
        email_bp=vacante.email_bp,
        id_pos=vacante.id_pos,
        deno_pos=vacante.deno_pos,
        id_fun=vacante.id_fun,
        deno_fun=vacante.deno_fun,
        ar_per=vacante.ar_per,
        sueldo_via_planta_76=vacante.sueldo_via_planta_76,
        sueldo_planta_80=vacante.sueldo_planta_80,
        sueldo_propuesta_especial=None,
        id_reclutador=vacante.id_reclutador,
        nombre_reclutador=reclutador.full_name if reclutador else None,
        anio=vacante.anio,
        mes=vacante.mes,
        fecha=vacante.fecha,
        fecha_solicitud_vacante=vacante.fecha_solicitud_vacante,
        estatus_rys="Creación",
        dir_corp=vacante.dir_corp,
        bp_is_tracked=True,
        
    )
    # if position
    session.add(vacante)
    session.commit()
    session.refresh(vacante)
    session.add(vacante_history)
    session.commit()
    return vacante


@router.put("/{id}", response_model=VacantePublic)
def update_vacante(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: str,
    vacante_in: VacanteUpdate,
) -> Any:
    """
    Update a vacante.
    """
    vacante = session.get(Vacante, id)

    # set bp tracking to True
    vacante.bp_is_tracked = True

    # update reclutador fields if id_reclutador is provided
    if vacante_in.id_reclutador:
        reclutador = session.get(User, vacante_in.id_reclutador)
        if not reclutador:
            raise HTTPException(status_code=404, detail="Reclutador no encontrado")
        vacante.nombre_reclutador = reclutador.full_name
        vacante.email_reclutador = reclutador.email
    # make sure sueldo_propuesta_especial is an integer
    # if vacante_in.sueldo_propuesta_especial:
    #     vacante_in.sueldo_propuesta_especial = int(vacante_in.sueldo_propuesta_especial)
    # find catalogo_posicion and catalogo_funcion
    if vacante_in.id_pos:
        try:
            pos = session.get(CatalogoPosicion, vacante_in.id_pos)
            vacante.deno_pos = pos.deno_pos
        except AttributeError:
            vacante.deno_pos = "Posición no encontrada"
    if vacante_in.id_fun:
        try:
            fun = session.get(CatalogoFuncion, vacante_in.id_fun)
            vacante.deno_fun = fun.deno_fun
        except AttributeError:
            vacante.deno_fun = "Función no encontrada"
    # find catalogo_ceco
    if vacante_in.id_ceco:
        try:
            ceco = session.get(CatalogoCeco, vacante_in.id_ceco)
            vacante.nivel1 = ceco.nivel1
            vacante.nivel2 = ceco.nivel2
            vacante.nivel3 = ceco.nivel3
        except AttributeError:
            vacante.nivel1 = "CECO no encontrado"
            vacante.nivel2 = "CECO no encontrado"
            vacante.nivel3 = "CECO no encontrado"

    # map txt_ubi ceco with CATALOGO_UBICACIONES
    if vacante_in.ubi_ceco:
        vacante.txt_ubi_ceco = CATALOGO_UBICACIONES.get(
            vacante_in.ubi_ceco, "Ubicación no encontrada"
        )

    if not vacante:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")
    if not current_user.is_superuser and (vacante.id_bp != current_user.id):
        raise HTTPException(status_code=400, detail="Sin permisos suficientes")
    update_dict = vacante_in.model_dump(exclude_unset=True)
    vacante.sqlmodel_update(update_dict)
    session.add(vacante)
    session.commit()
    session.refresh(vacante)
    return vacante


@router.put("/rys/{id}", response_model=VacantePublic)
def update_vacante_rys(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: str,
    vacante_in: VacanteUpdateRys,
) -> Any:
    """
    Update a vacante RYS.
    """
    vacante = session.get(Vacante, id)

    if not vacante:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")
    if not current_user.is_superuser and (vacante.id_reclutador != current_user.id):
        raise HTTPException(status_code=400, detail="Sin permisos suficientes")

    vacante.rys_is_tracked = True
    # if estatus_rys is different from the previous one, create a new history record
    if vacante_in.estatus_rys != vacante.estatus_rys:
        vacante_history = VacanteHistory(
            id=uuid4().hex,
            id_vacante=vacante.id,
            id_bp=vacante.id_bp,
            nombre_bp=vacante.nombre_bp,
            email_bp=vacante.email_bp,
            id_pos=vacante.id_pos,
            deno_pos=vacante.deno_pos,
            id_fun=vacante.id_fun,
            deno_fun=vacante.deno_fun,
            ar_per=vacante.ar_per,
            sueldo_via_planta_76=vacante.sueldo_via_planta_76,
            sueldo_planta_80=vacante.sueldo_planta_80,
            sueldo_propuesta_especial=vacante.sueldo_propuesta_especial,
            id_reclutador=vacante.id_reclutador,
            nombre_reclutador=vacante.nombre_reclutador,
            anio=vacante.anio,
            mes=vacante.mes,
            fecha=vacante.fecha,
            fecha_solicitud_vacante=vacante.fecha_solicitud_vacante,
            estatus_rys=vacante_in.estatus_rys,
            quien_cancela=vacante_in.quien_cancela,
            nota_cancelacion=vacante_in.nota_cancelacion,
            id_quien_cambio=current_user.id,
            dir_corp=vacante.dir_corp,
        )
        session.add(vacante_history)

    update_dict = vacante_in.model_dump(exclude_unset=True)
    vacante.sqlmodel_update(update_dict)

    session.add(vacante)

    session.commit()
    session.refresh(vacante)
    return vacante


@router.put("/reinicio/{id}", response_model=VacantePublic)
def update_vacante_reinicio(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: str,
    vacante_in: VacanteUpdateReinicio,
) -> Any:
    """
    Restart a vacante RYS.
    """
    vacante = session.get(Vacante, id)

    if not vacante:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")
    if not current_user.is_superuser and (vacante.id_reclutador != current_user.id):
        raise HTTPException(status_code=400, detail="Sin permisos suficientes")
    # if motivo_reinicio is provided, create a new history record and restart the vacante

    vacante.rys_is_tracked = True
    vacante_reinicio = VacanteReinicio(
        id=uuid4().hex,
        id_vacante=vacante.id,
        anio=vacante.anio,
        mes=vacante.mes,
        id_pos=vacante.id_pos,
        id_fun=vacante.id_fun,
        id_ceco=vacante.id_ceco,
        ubi_ceco=vacante.ubi_ceco,
        gpo_per=vacante.gpo_per,
        ar_per=vacante.ar_per,
        jefe_inmediato=vacante.jefe_inmediato,
        sociedad=vacante.sociedad,
        dir_corp=vacante.dir_corp,
        tipo_vacante=vacante.tipo_vacante,
        sueldo_via_planta_76=vacante.sueldo_via_planta_76,
        sueldo_planta_80=vacante.sueldo_planta_80,
        deno_pos=vacante.deno_pos,
        fecha=vacante.fecha,
        id_bp=vacante.id_bp,
        nombre_bp=vacante.nombre_bp,
        email_bp=vacante.email_bp,
        deno_fun=vacante.deno_fun,
        nivel1=vacante.nivel1,
        nivel2=vacante.nivel2,
        nivel3=vacante.nivel3,
        sueldo_propuesta_especial=vacante.sueldo_propuesta_especial,
        propuesta_especial_inicio=vacante.propuesta_especial_inicio,
        fecha_solicitud_vacante=vacante.fecha_solicitud_vacante,
        id_reclutador=vacante.id_reclutador,
        nombre_reclutador=vacante.nombre_reclutador,
        email_reclutador=vacante.email_reclutador,
        estatus_rys=vacante.estatus_rys,
        quien_cancela=vacante.quien_cancela,
        nota_cancelacion=vacante.nota_cancelacion,
        complejidad=vacante.complejidad,
        solicitud_cita_acuerdo_de_Servicio=vacante.solicitud_cita_acuerdo_de_Servicio,
        acuerdo_de_servicio=vacante.acuerdo_de_servicio,
        fecha_entrega_candidatos1=vacante.fecha_entrega_candidatos1,
        fecha_entrega_candidatos2=vacante.fecha_entrega_candidatos2,
        fecha_entrega_candidatos3=vacante.fecha_entrega_candidatos3,
        entrevista_area1=vacante.entrevista_area1,
        entrevista_area2=vacante.entrevista_area2,
        entrevista_area3=vacante.entrevista_area3,
        seleccion_de_candidato=vacante.seleccion_de_candidato,
        cierra_proceso=vacante.cierra_proceso,
        fecha_ingreso=vacante.fecha_ingreso,
        motivo_reinicio=vacante_in.motivo_reinicio,
    )
    session.add(vacante_reinicio)

    # restart just rys fields from current vacante
    vacante.estatus_rys = "Reinicio"
    vacante.quien_cancela = None
    vacante.nota_cancelacion = None
    vacante.solicitud_cita_acuerdo_de_Servicio = None
    vacante.acuerdo_de_servicio = None
    vacante.fecha_entrega_candidatos1 = None
    vacante.fecha_entrega_candidatos2 = None
    vacante.fecha_entrega_candidatos3 = None
    vacante.entrevista_area1 = None
    vacante.entrevista_area2 = None
    vacante.entrevista_area3 = None
    vacante.seleccion_de_candidato = None
    vacante.cierra_proceso = None
    vacante.fecha_ingreso = None
    vacante.motivo_reinicio = None
    session.add(vacante)

    session.commit()
    session.refresh(vacante)
    return vacante


@router.delete("/{id}")
def delete_vacante(session: SessionDep, current_user: CurrentUser, id: str) -> Message:
    """
    Delete a vacante.
    """
    vacante = session.get(Vacante, id)

    if not vacante:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")
    if not current_user.is_superuser and (vacante.id_bp != current_user.id):
        raise HTTPException(status_code=400, detail="Sin permisos suficientes")

    vacante.rys_is_tracked = True
    vacante.bp_is_tracked = True
    # Create a new history record for the vacante
    vacante_history = VacanteHistory(
        id=uuid4().hex,
        id_vacante=vacante.id,
        id_bp=vacante.id_bp,
        nombre_bp=vacante.nombre_bp,
        email_bp=vacante.email_bp,
        id_pos=vacante.id_pos,
        deno_pos=vacante.deno_pos,
        id_fun=vacante.id_fun,
        deno_fun=vacante.deno_fun,
        ar_per=vacante.ar_per,
        sueldo_via_planta_76=vacante.sueldo_via_planta_76,
        sueldo_planta_80=vacante.sueldo_planta_80,
        sueldo_propuesta_especial=vacante.sueldo_propuesta_especial,
        id_reclutador=vacante,
        nombre_reclutador=vacante.nombre_reclutador,
        anio=vacante.anio,
        mes=vacante.mes,
        fecha=vacante.fecha,
        fecha_solicitud_vacante=vacante.fecha_solicitud_vacante,
        estatus_rys="Eliminada",
    )
    session.delete(vacante)
    session.commit()
    session.add(vacante_history)
    session.commit()
    return Message(message="Vacante eliminada")
