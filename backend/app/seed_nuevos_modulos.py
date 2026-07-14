"""
Seed para nuevos modulos, tipos de documento, subtipos, ejercicios, etc.
Se ejecuta independientemente del seed original (no salta si empresa existe).
"""
import asyncio
from datetime import date
from sqlalchemy import select, text
from app.core.database import async_session as AsyncSessionLocal
from app.domain.models.empresa import Empresa
from app.domain.models.ejercicio import EjercicioFiscal
from app.domain.models.document_type import ModuloSistema
from app.domain.models.permiso import Permiso
from app.seeds.seed_modulos import seed_modulos
from app.domain.accounting.seed_classifications import seed_classifications


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Empresa).where(Empresa.ruc == "TUCK001"))
        emp = result.scalar_one_or_none()
        if not emp:
            print("ERROR: Empresa Tuckler no encontrada. Ejecuta seed.py primero.")
            return

        # Seed classifications si no existen
        await seed_classifications(db)

        # Seed modulos, tipos documento, subtipos, permisos
        await seed_modulos(db, emp.id)

        # Seed ejercicio fiscal 2026 si no existe
        existing_ej = await db.execute(
            select(EjercicioFiscal).where(
                EjercicioFiscal.company_id == emp.id,
                EjercicioFiscal.codigo == '2026'
            )
        )
        if not existing_ej.scalar_one_or_none():
            ej = EjercicioFiscal(
                company_id=emp.id,
                codigo='2026',
                nombre='Ejercicio 2026',
                fecha_inicio=date(2026, 1, 1),
                fecha_fin=date(2026, 12, 31),
                cerrado=False,
            )
            db.add(ej)

        # Asignar todos los permisos al rol ADMIN
        admin_rol = await db.execute(
            text("SELECT id FROM rol WHERE empresa_id = :eid AND nombre = 'ADMIN'"),
            {"eid": emp.id},
        )
        admin_rol_id = admin_rol.scalar_one_or_none()
        if admin_rol_id:
            permisos = await db.execute(select(Permiso))
            for p in permisos.scalars().all():
                exists = await db.execute(
                    text("SELECT 1 FROM rol_permiso WHERE rol_id = :rol_id AND permiso_id = :permiso_id"),
                    {"rol_id": admin_rol_id, "permiso_id": p.id},
                )
                if not exists.scalar():
                    await db.execute(
                        text("INSERT INTO rol_permiso (rol_id, permiso_id) VALUES (:rol_id, :permiso_id)"),
                        {"rol_id": admin_rol_id, "permiso_id": p.id},
                    )

        await db.commit()
        print("Seed de nuevos modulos completado exitosamente.")


if __name__ == "__main__":
    asyncio.run(main())
