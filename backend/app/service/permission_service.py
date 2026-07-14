import uuid
from sqlalchemy import select, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.permiso import Permiso, UsuarioPermiso
from app.domain.models.asociaciones import rol_permiso, usuario_rol


async def user_has_perm(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    perm_codigo: str,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
) -> bool:
    """
    Unified permission check. Checks:
    1. Role-based permissions (user → roles → permissions)
    2. Direct user permissions (usuario_permiso)
    3. Entity-scoped permissions if entity_type + entity_id provided

    Returns True if ANY of these grant access and none explicitly deny it.
    """
    perm = await db.execute(
        select(Permiso.id, Permiso.modulo, Permiso.action_type).where(Permiso.codigo == perm_codigo)
    )
    row = perm.one_or_none()
    if not row:
        return False
    perm_id = row.id
    modulo = row.modulo
    action_type = row.action_type

    # 1. Check role-based permissions
    has_role_perm = await db.execute(
        select(usuario_rol).where(usuario_rol.c.usuario_id == usuario_id).limit(1)
    )
    if has_role_perm.first():
        rp = await db.execute(
            select(rol_permiso.c.permiso_id).where(
                rol_permiso.c.rol_id.in_(
                    select(usuario_rol.c.rol_id).where(usuario_rol.c.usuario_id == usuario_id)
                ),
                rol_permiso.c.permiso_id == perm_id,
            ).limit(1)
        )
        if rp.first():
            # Check for explicit deny via direct user perm (override)
            if entity_type:
                deny = await db.execute(
                    select(UsuarioPermiso).where(
                        UsuarioPermiso.usuario_id == usuario_id,
                        UsuarioPermiso.permiso_id == perm_id,
                        UsuarioPermiso.entity_type == entity_type,
                        UsuarioPermiso.entity_id == entity_id,
                        UsuarioPermiso.allow == False,
                    ).limit(1)
                )
                if deny.first():
                    return False
            return True

    # 2. Check direct user permissions (global or entity-scoped)
    q = select(UsuarioPermiso).where(
        UsuarioPermiso.usuario_id == usuario_id,
        UsuarioPermiso.permiso_id == perm_id,
        UsuarioPermiso.allow == True,
    )
    if entity_type is not None and entity_id is not None:
        q = q.where(
            UsuarioPermiso.entity_type == entity_type,
            UsuarioPermiso.entity_id == entity_id,
        )
    else:
        q = q.where(UsuarioPermiso.entity_type.is_(None))
    q = q.limit(1)
    direct = await db.execute(q)
    return direct.first() is not None


async def get_user_permissions(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
) -> list[str]:
    """Returns all permission codes the user has (role-based + direct)."""
    # Role-based permission codes
    role_codes = await db.execute(
        select(Permiso.codigo).where(
            Permiso.id.in_(
                select(rol_permiso.c.permiso_id).where(
                    rol_permiso.c.rol_id.in_(
                        select(usuario_rol.c.rol_id).where(usuario_rol.c.usuario_id == usuario_id)
                    )
                )
            )
        )
    )
    codes = set(r[0] for r in role_codes.fetchall())

    # Direct user permissions (global)
    direct = await db.execute(
        select(Permiso.codigo).where(
            Permiso.id.in_(
                select(UsuarioPermiso.permiso_id).where(
                    UsuarioPermiso.usuario_id == usuario_id,
                    UsuarioPermiso.entity_type.is_(None),
                    UsuarioPermiso.allow == True,
                )
            )
        )
    )
    codes.update(r[0] for r in direct.fetchall())

    # Entity-scoped direct permissions
    if entity_type and entity_id:
        entity_codes = await db.execute(
            select(Permiso.codigo).where(
                Permiso.id.in_(
                    select(UsuarioPermiso.permiso_id).where(
                        UsuarioPermiso.usuario_id == usuario_id,
                        UsuarioPermiso.entity_type == entity_type,
                        UsuarioPermiso.entity_id == entity_id,
                        UsuarioPermiso.allow == True,
                    )
                )
            )
        )
        codes.update(r[0] for r in entity_codes.fetchall())

    return sorted(codes)
