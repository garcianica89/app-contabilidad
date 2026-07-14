"""
Migraciones para tablas existentes que SQLAlchemy create_all no altera.
Agrega nuevas columnas a tablas que ya existen en la BD.
"""
import asyncio
from sqlalchemy import text
from app.core.database import async_session


async def column_exists(db, table, column):
    r = await db.execute(text(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = '{table}' AND column_name = '{column}'
    """))
    return r.scalar() is not None


async def safe_alter(db, sql, desc):
    try:
        await db.execute(text(sql))
        print(f"  OK: {desc}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"  SKIP: {desc} (already exists)")
        else:
            print(f"  ERROR: {desc} - {e}")
            raise


async def main():
    async with async_session() as db:
        # --- numeracion ---
        if not await column_exists(db, 'numeracion', 'prefijo'):
            await safe_alter(db, "ALTER TABLE numeracion ADD COLUMN prefijo VARCHAR(20)", "numeracion.prefijo")
        if not await column_exists(db, 'numeracion', 'sufijo'):
            await safe_alter(db, "ALTER TABLE numeracion ADD COLUMN sufijo VARCHAR(20)", "numeracion.sufijo")
        if not await column_exists(db, 'numeracion', 'digitos'):
            await safe_alter(db, "ALTER TABLE numeracion ADD COLUMN digitos INTEGER DEFAULT 6", "numeracion.digitos")
        if not await column_exists(db, 'numeracion', 'reinicio'):
            await safe_alter(db, "ALTER TABLE numeracion ADD COLUMN reinicio VARCHAR(20) DEFAULT 'NUNCA'", "numeracion.reinicio")
        if not await column_exists(db, 'numeracion', 'numeracion_manual'):
            await safe_alter(db, "ALTER TABLE numeracion ADD COLUMN numeracion_manual BOOLEAN DEFAULT FALSE", "numeracion.numeracion_manual")
        if not await column_exists(db, 'numeracion', 'permite_reserva'):
            await safe_alter(db, "ALTER TABLE numeracion ADD COLUMN permite_reserva BOOLEAN DEFAULT FALSE", "numeracion.permite_reserva")
        if not await column_exists(db, 'numeracion', 'sucursal_id'):
            await safe_alter(db, "ALTER TABLE numeracion ADD COLUMN sucursal_id UUID REFERENCES sucursal(id)", "numeracion.sucursal_id")

        # --- asiento ---
        if not await column_exists(db, 'asiento', 'numero'):
            # ya existe pero es integer, cambiar a string no es trivial via ALTER
            print("  SKIP: asiento.numero (cambio de int a string requiere migracion manual)")
        if not await column_exists(db, 'asiento', 'journal_type_id'):
            await safe_alter(db, "ALTER TABLE asiento ADD COLUMN journal_type_id UUID REFERENCES journal_type(id)", "asiento.journal_type_id")
        if not await column_exists(db, 'asiento', 'documento_tipo'):
            await safe_alter(db, "ALTER TABLE asiento ADD COLUMN documento_tipo VARCHAR(30)", "asiento.documento_tipo")
        if not await column_exists(db, 'asiento', 'documento_id'):
            await safe_alter(db, "ALTER TABLE asiento ADD COLUMN documento_id UUID", "asiento.documento_id")
        if not await column_exists(db, 'asiento', 'estado'):
            await safe_alter(db, "ALTER TABLE asiento ADD COLUMN estado VARCHAR(20) DEFAULT 'BORRADOR'", "asiento.estado")

        # --- asiento_linea ---
        if not await column_exists(db, 'asiento_linea', 'debe'):
            await safe_alter(db, "ALTER TABLE asiento_linea ADD COLUMN debe NUMERIC(14,2) DEFAULT 0", "asiento_linea.debe")
        if not await column_exists(db, 'asiento_linea', 'haber'):
            await safe_alter(db, "ALTER TABLE asiento_linea ADD COLUMN haber NUMERIC(14,2) DEFAULT 0", "asiento_linea.haber")
        if not await column_exists(db, 'asiento_linea', 'cuenta_id_old'):
            # asiento_linea ya tiene cuenta_id y debe_local/haber_local de la vieja estructura
            print("  SKIP: asiento_linea.cuenta_id ya existe")

        await db.commit()
        print("Migraciones completadas.")


if __name__ == "__main__":
    asyncio.run(main())
