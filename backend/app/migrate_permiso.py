"""
Migracion para agregar nuevas columnas a la tabla permiso.
SQLAlchemy create_all no altera tablas existentes.
"""
import asyncio
from sqlalchemy import text
from app.core.database import async_session


async def main():
    async with async_session() as db:
        # Verificar si la columna module_id ya existe
        result = await db.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'permiso' AND column_name = 'module_id'
        """))
        if not result.scalar():
            await db.execute(text("""
                ALTER TABLE permiso
                ADD COLUMN module_id UUID REFERENCES modulo_sistema(id),
                ADD COLUMN action_type VARCHAR(50),
                ADD COLUMN scope VARCHAR(20) DEFAULT 'ALL'
            """))
            await db.commit()
            print("Columnas agregadas a permiso: module_id, action_type, scope")
        else:
            print("Columnas ya existen en permiso")


if __name__ == "__main__":
    asyncio.run(main())
