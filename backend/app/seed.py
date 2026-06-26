import uuid
from datetime import date, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.domain.models.empresa import Empresa
from app.domain.models.usuario import Usuario
from app.domain.models.rol import Rol
from app.domain.models.permiso import Permiso
from app.domain.models.moneda import Moneda
from app.domain.models.periodo import PeriodoContable
from app.domain.models.cuenta_contable import CuentaContable
from app.domain.models.asiento import Asiento, AsientoLinea
from app.domain.models.categoria import Categoria
from app.domain.models.producto import Producto
from app.domain.models.cliente import Cliente
from app.domain.models.proveedor import Proveedor
from app.domain.models.caja import Caja, MovimientoCaja


async def seed_database(db: AsyncSession):
    empresa = await db.execute(select(Empresa).where(Empresa.ruc == "TUCK001"))
    if empresa.scalar_one_or_none():
        return

    moneda_nio = await db.execute(select(Moneda).where(Moneda.codigo == "NIO"))
    moneda_nio = moneda_nio.scalar_one_or_none()
    if not moneda_nio:
        moneda_nio = Moneda(
            codigo="NIO", nombre="Cordoba Nicaraguense", simbolo="C$",
            tasa_cambio=1.0, es_base=True, activa=True,
        )
        db.add(moneda_nio)

    moneda_usd = await db.execute(select(Moneda).where(Moneda.codigo == "USD"))
    moneda_usd = moneda_usd.scalar_one_or_none()
    if not moneda_usd:
        moneda_usd = Moneda(
            codigo="USD", nombre="Dolar Estadounidense", simbolo="U$",
            tasa_cambio=36.6243, es_base=False, activa=True,
        )
        db.add(moneda_usd)

    await db.flush()

    emp = Empresa(
        nombre="Tuckler Beauty",
        nombre_legal="Tuckler Beauty, S.A.",
        ruc="TUCK001",
        direccion="Managua, Nicaragua",
        telefono="505-8888-8888",
        email="info@tucklerbeauty.com",
        moneda_local_id=moneda_nio.id,
    )
    db.add(emp)
    await db.flush()

    admin_rol = Rol(empresa_id=emp.id, nombre="ADMIN", descripcion="Administrador del sistema")
    db.add(admin_rol)
    await db.flush()

    result = await db.execute(select(Permiso))
    permisos = result.scalars().all()

    for p in permisos:
        exists = await db.execute(
            text("SELECT 1 FROM rol_permiso WHERE rol_id = :rol_id AND permiso_id = :permiso_id"),
            {"rol_id": admin_rol.id, "permiso_id": p.id},
        )
        if not exists.scalar():
            await db.execute(
                text("INSERT INTO rol_permiso (rol_id, permiso_id) VALUES (:rol_id, :permiso_id)"),
                {"rol_id": admin_rol.id, "permiso_id": p.id},
            )

    master = Usuario(
        empresa_id=emp.id,
        username="rgarcia",
        email="rgarcia@tucklerbeauty.com",
        password_hash=hash_password("exrgarcia"),
        nombre_completo="Ramon Garcia",
        activo=True,
    )
    db.add(master)
    await db.flush()

    await db.execute(
        text("INSERT INTO usuario_rol (usuario_id, rol_id) VALUES (:uid, :rid) ON CONFLICT DO NOTHING"),
        {"uid": master.id, "rid": admin_rol.id},
    )

    periodo = PeriodoContable(
        empresa_id=emp.id,
        codigo="2026-01",
        nombre="Enero 2026",
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 31),
        cerrado=False,
    )
    db.add(periodo)

    periodo2 = PeriodoContable(
        empresa_id=emp.id,
        codigo="2026-02",
        nombre="Febrero 2026",
        fecha_inicio=date(2026, 2, 1),
        fecha_fin=date(2026, 2, 28),
        cerrado=False,
    )
    db.add(periodo2)

    periodo3 = PeriodoContable(
        empresa_id=emp.id,
        codigo="2026-03",
        nombre="Marzo 2026",
        fecha_inicio=date(2026, 3, 1),
        fecha_fin=date(2026, 3, 31),
        cerrado=False,
    )
    db.add(periodo3)
    await db.flush()

    caja_general = Caja(
        empresa_id=emp.id, nombre="Caja General", moneda_id=moneda_nio.id,
        saldo_actual=6290, activa=True,
    )
    db.add(caja_general)

    asiento_apertura = Asiento(
        empresa_id=emp.id, periodo_id=periodo.id, numero=1,
        tipo="APERTURA", concepto="Aporte inicial de capital",
        fecha=date(2026, 1, 1),
    )
    db.add(asiento_apertura)
    await db.flush()

    cta_caja = await db.execute(
        select(CuentaContable).where(
            CuentaContable.empresa_id == emp.id,
            CuentaContable.codigo == "1-1-1-1-01-00-00-0000",
        )
    )
    cta_capital = await db.execute(
        select(CuentaContable).where(
            CuentaContable.empresa_id == emp.id,
            CuentaContable.codigo == "3-1-1-0-00-00-0000",
        )
    )

    db.add_all([
        AsientoLinea(
            asiento_id=asiento_apertura.id, cuenta_id=cta_caja.scalar_one().id,
            descripcion="Aporte inicial", debe_local=6290, haber_local=0,
        ),
        AsientoLinea(
            asiento_id=asiento_apertura.id, cuenta_id=cta_capital.scalar_one().id,
            descripcion="Capital social inicial", debe_local=0, haber_local=6290,
        ),
    ])

    db.add(MovimientoCaja(
        empresa_id=emp.id, caja_id=caja_general.id,
        fecha=date(2026, 1, 1), tipo="APERTURA",
        concepto="Aporte inicial de capital",
        entrada=6290, salida=0, saldo=6290,
        asiento_id=asiento_apertura.id,
    ))

    categoria_zapatos = Categoria(empresa_id=emp.id, nombre="Zapatos")
    categoria_ropa = Categoria(empresa_id=emp.id, nombre="Ropa")
    categoria_accesorios = Categoria(empresa_id=emp.id, nombre="Accesorios")
    db.add_all([categoria_zapatos, categoria_ropa, categoria_accesorios])
    await db.flush()

    productos_data = [
        ("SANDALIAS", "Sandalias", categoria_zapatos.id, 200, 300),
        ("ZAPATOS-BA", "Zapatos Bajos", categoria_zapatos.id, 300, 450),
        ("ZAPATOS-AL", "Zapatos Altos", categoria_zapatos.id, 350, 500),
        ("ZAPATOS-TA", "Zapatos Tacon", categoria_zapatos.id, 400, 600),
        ("ZAPATOS-DP", "Zapatos Deportivos", categoria_zapatos.id, 250, 400),
        ("LEGGINGS", "Leggings", categoria_ropa.id, 150, 250),
        ("CAMISAS", "Camisas", categoria_ropa.id, 180, 280),
        ("CONJUNTOS", "Conjuntos", categoria_ropa.id, 350, 550),
    ]
    for cod, nom, cat_id, costo, precio in productos_data:
        db.add(Producto(
            empresa_id=emp.id, codigo=cod, nombre=nom, categoria_id=cat_id,
            costo_promedio=costo, precio_venta=precio, stock_actual=0, stock_minimo=5,
        ))

    db.add(Cliente(empresa_id=emp.id, codigo="C001", nombre="Cliente General", saldo=0))

    db.add(Proveedor(empresa_id=emp.id, codigo="P001", nombre="Proveedor General", saldo=0, plazo_credito=30))

    cuentas_data = [
        ("1-0-0-0-00-00-00-0000", "ACTIVO", "ACTIVO", 1, False),
        ("1-1-0-0-00-00-00-0000", "ACTIVO CORRIENTE", "ACTIVO", 2, False),
        ("1-1-1-0-00-00-00-0000", "EFECTIVO Y EQUIVALENTES", "ACTIVO", 3, False),
        ("1-1-1-1-00-00-00-0000", "CAJA", "ACTIVO", 4, False),
        ("1-1-1-1-01-00-00-0000", "Caja General", "ACTIVO", 5, True),
        ("1-1-2-0-00-00-00-0000", "CUENTAS POR COBRAR", "ACTIVO", 3, False),
        ("1-1-2-1-00-00-00-0000", "CLIENTES", "ACTIVO", 4, False),
        ("1-1-2-1-01-00-00-0000", "Cuentas por Cobrar", "ACTIVO", 5, True),
        ("1-1-3-0-00-00-00-0000", "INVENTARIOS", "ACTIVO", 3, False),
        ("1-1-3-1-00-00-00-0000", "PRODUCTOS PARA LA VENTA", "ACTIVO", 4, False),
        ("1-1-3-1-01-00-00-0000", "Inventario de Mercancias", "ACTIVO", 5, True),
        ("2-0-0-0-00-00-00-0000", "PASIVO", "PASIVO", 1, False),
        ("2-1-0-0-00-00-00-0000", "PASIVO CORRIENTE", "PASIVO", 2, False),
        ("2-1-1-0-00-00-00-0000", "CUENTAS POR PAGAR", "PASIVO", 3, False),
        ("2-1-1-1-00-00-00-0000", "PROVEEDORES", "PASIVO", 4, False),
        ("2-1-1-1-01-00-00-0000", "Cuentas por Pagar", "PASIVO", 5, True),
        ("2-1-2-0-00-00-00-0000", "IMPUESTOS POR PAGAR", "PASIVO", 3, False),
        ("2-1-2-1-00-00-00-0000", "IVA por Pagar", "PASIVO", 5, True),
        ("2-1-2-2-00-00-00-0000", "IR por Pagar", "PASIVO", 5, True),
        ("3-0-0-0-00-00-00-0000", "PATRIMONIO", "PATRIMONIO", 1, False),
        ("3-1-0-0-00-00-00-0000", "CAPITAL", "PATRIMONIO", 2, False),
        ("3-1-1-0-00-00-00-0000", "Capital Social", "PATRIMONIO", 5, True),
        ("3-1-2-0-00-00-00-0000", "Resultado del Ejercicio", "PATRIMONIO", 5, True),
        ("4-0-0-0-00-00-00-0000", "INGRESOS", "INGRESO", 1, False),
        ("4-1-0-0-00-00-00-0000", "INGRESOS OPERACIONALES", "INGRESO", 2, False),
        ("4-1-1-0-00-00-00-0000", "VENTAS", "INGRESO", 3, False),
        ("4-1-1-1-00-00-00-0000", "Ventas de Mercancias", "INGRESO", 4, False),
        ("4-1-1-1-01-00-00-0000", "Ventas al Contado", "INGRESO", 5, True),
        ("4-1-1-1-02-00-00-0000", "Ventas al Credito", "INGRESO", 5, True),
        ("5-0-0-0-00-00-00-0000", "COSTOS", "COSTO", 1, False),
        ("5-1-0-0-00-00-00-0000", "COSTOS DE VENTA", "COSTO", 2, False),
        ("5-1-1-0-00-00-00-0000", "COSTO DE MERCANCIAS", "COSTO", 3, False),
        ("5-1-1-1-00-00-00-0000", "Costo de Ventas", "COSTO", 4, False),
        ("5-1-1-1-01-00-00-0000", "Costo de Ventas", "COSTO", 5, True),
        ("6-0-0-0-00-00-00-0000", "GASTOS", "GASTO", 1, False),
        ("6-1-0-0-00-00-00-0000", "GASTOS OPERACIONALES", "GASTO", 2, False),
        ("6-1-1-0-00-00-00-0000", "GASTOS DE ADMINISTRACION", "GASTO", 3, False),
        ("6-1-1-1-00-00-00-0000", "Sueldos y Salarios", "GASTO", 5, True),
        ("6-1-1-2-00-00-00-0000", "Alquileres", "GASTO", 5, True),
        ("6-1-1-3-00-00-00-0000", "Servicios Basicos", "GASTO", 5, True),
        ("6-1-1-4-00-00-00-0000", "Otros Gastos", "GASTO", 5, True),
    ]

    padre_map = {}
    for codigo, nombre, tipo, nivel, acepta in cuentas_data:
        padre_id = None
        if nivel > 1:
            padre_cod = "-".join(codigo.split("-")[:nivel-1]) + "-" + "00" * 2 + "-0000"
            padre_cod = padre_cod.rstrip("-")
            # Build the parent code
            parts = codigo.split("-")
            parent_parts = parts[:nivel-1]
            while len(parent_parts) < 8:
                parent_parts.append("00" if len(parent_parts) < 6 else "0000")
            padre_cod = "-".join(parent_parts)
            padre_id = padre_map.get(padre_cod)

            if not padre_id and nivel == 2:
                root_code = codigo.split("-")[0] + "-0-0-0-00-00-00-0000"
                root_parts = codigo.split("-")
                root_p = [root_parts[0]] + ["0"]*7
                root_code = "-".join(root_p)
                if root_code in padre_map:
                    padre_id = padre_map[root_code]

        new_parts = list(codigo.split("-"))
        while len(new_parts) < 8:
            new_parts.append("00" if len(new_parts) < 6 else "0000")
        full_code = "-".join(new_parts)

        cuenta = CuentaContable(
            empresa_id=emp.id, codigo=full_code, nombre=nombre,
            tipo=tipo, nivel=nivel, padre_id=padre_id,
            acepta_datos=acepta, activa=True,
        )
        db.add(cuenta)
        await db.flush()
        padre_map[full_code] = cuenta.id

    await db.commit()
    print("Base de datos inicializada con datos semilla")
