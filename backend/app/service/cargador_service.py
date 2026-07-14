import csv
import io
import re
import hashlib
import tempfile
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.banco import CuentaBanco, MovimientoBanco
from app.domain.models.conciliacion import ConciliacionBancaria, PartidaConciliacion
from app.domain.models.document_type import DocumentoSubtipo


class MovimientoParseado:
    def __init__(
        self,
        fecha: date,
        concepto: str,
        monto: float,
        referencia: Optional[str] = None,
        saldo: Optional[float] = None,
        tipo: Optional[str] = None,
        subtipo_codigo: Optional[str] = None,
        idx: int = 0,
        raw: Optional[dict] = None,
    ):
        self.fecha = fecha
        self.concepto = concepto
        self.monto = monto
        self.referencia = referencia
        self.saldo = saldo
        self.tipo = tipo
        self.subtipo_codigo = subtipo_codigo
        self.idx = idx
        self.raw = raw or {}
        self.duplicado = False
        self.subtipo_id = None
        self.numero_subtipo = None

    @property
    def abs_monto(self) -> float:
        return abs(self.monto)

    @property
    def es_ingreso(self) -> bool:
        return self.monto >= 0

    @property
    def hash(self) -> str:
        raw = f"{self.fecha.isoformat()}|{self.concepto}|{self.monto}|{self.referencia or ''}|{self.subtipo_codigo or ''}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "idx": self.idx,
            "fecha": self.fecha.isoformat(),
            "concepto": self.concepto,
            "monto": self.monto,
            "referencia": self.referencia,
            "saldo": self.saldo,
            "tipo": self.tipo,
            "subtipo_codigo": self.subtipo_codigo,
            "abs_monto": self.abs_monto,
            "es_ingreso": self.es_ingreso,
            "hash": self.hash,
            "duplicado": self.duplicado,
        }


COLUMNAS_EXCEL = {
    "fecha": ["fecha", "date", "fecha_mov", "fecha_movimiento"],
    "concepto": ["concepto", "descripcion", "detalle", "glosa", "description"],
    "monto": ["monto", "valor", "importe", "amount", "cargos", "abonos"],
    "referencia": ["referencia", "ref", "nro_doc", "numero_documento", "numero", "doc"],
    "saldo": ["saldo", "balance"],
    "subtipo_codigo": ["subtipo", "subtipo_codigo", "tipo_mov", "codigo_mov", "codigo"],
    "tipo": ["tipo", "tipo_movimiento", "naturaleza", "signo"],
}


def _encontrar_columna(headers: List[str], posibles: List[str]) -> Optional[str]:
    h_lower = [h.lower().strip() for h in headers]
    for posible in posibles:
        for i, h in enumerate(h_lower):
            if h == posible or h.startswith(posible):
                return headers[i]
    return None


def _parse_fecha(valor) -> Optional[date]:
    if isinstance(valor, date):
        return valor
    if isinstance(valor, datetime):
        return valor.date()
    s = str(valor).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_monto(valor) -> float:
    if isinstance(valor, (int, float)):
        return float(valor)
    s = str(valor).strip().replace(",", "").replace("$", "").replace(" ", "")
    if not s:
        return 0
    # si tiene dos columnas cargos/abonos, usamos diferencia
    return float(s)


class CargadorService:

    @staticmethod
    def parsear_excel(ruta: str) -> List[MovimientoParseado]:
        import openpyxl
        wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
        ws = wb.active

        filas = list(ws.iter_rows(values_only=False))
        if not filas:
            return []

        headers = [str(c.value or "").strip() for c in filas[0]]

        col_fecha = _encontrar_columna(headers, COLUMNAS_EXCEL["fecha"])
        col_concepto = _encontrar_columna(headers, COLUMNAS_EXCEL["concepto"])
        col_monto = _encontrar_columna(headers, COLUMNAS_EXCEL["monto"])
        col_ref = _encontrar_columna(headers, COLUMNAS_EXCEL["referencia"])
        col_saldo = _encontrar_columna(headers, COLUMNAS_EXCEL["saldo"])
        col_subtipo = _encontrar_columna(headers, COLUMNAS_EXCEL["subtipo_codigo"])
        col_tipo = _encontrar_columna(headers, COLUMNAS_EXCEL["tipo"])

        if not col_fecha or not col_concepto or not col_monto:
            raise ValueError(
                "El archivo Excel debe tener al menos las columnas: "
                "fecha, concepto, monto. Columnas encontradas: " + ", ".join(headers)
            )

        resultados = []
        for idx, row in enumerate(filas[1:]):
            if not any(c.value is not None for c in row):
                continue
            celdas = {headers[i]: (row[i].value if i < len(row) else None) for i in range(len(headers))}

            fecha = _parse_fecha(celdas.get(col_fecha))
            if not fecha:
                continue

            concepto = str(celdas.get(col_concepto, "") or "").strip()
            if not concepto:
                concepto = "Movimiento bancario"

            monto = _parse_monto(celdas.get(col_monto, 0))

            ref = str(celdas[col_ref]).strip() if col_ref and celdas.get(col_ref) else None
            saldo = _parse_monto(celdas[col_saldo]) if col_saldo and celdas.get(col_saldo) else None
            subtipo_codigo = str(celdas[col_subtipo]).strip() if col_subtipo and celdas.get(col_subtipo) else None
            tipo = str(celdas[col_tipo]).strip() if col_tipo and celdas.get(col_tipo) else None

            if subtipo_codigo and subtipo_codigo.lower() in ("none", "", "null"):
                subtipo_codigo = None

            resultados.append(MovimientoParseado(
                fecha=fecha,
                concepto=concepto,
                monto=monto,
                referencia=ref,
                saldo=saldo,
                tipo=tipo,
                subtipo_codigo=subtipo_codigo,
                idx=idx,
                raw=celdas,
            ))

        wb.close()
        return resultados

    @staticmethod
    def parsear_csv(
        contenido: str,
        delimitador: str = ",",
        tiene_encabezado: bool = True,
    ) -> List[MovimientoParseado]:
        reader = csv.DictReader(io.StringIO(contenido), delimiter=delimitador)
        headers = reader.fieldnames or []

        col_fecha = _encontrar_columna(headers, COLUMNAS_EXCEL["fecha"])
        col_concepto = _encontrar_columna(headers, COLUMNAS_EXCEL["concepto"])
        col_monto = _encontrar_columna(headers, COLUMNAS_EXCEL["monto"])
        col_ref = _encontrar_columna(headers, COLUMNAS_EXCEL["referencia"])
        col_saldo = _encontrar_columna(headers, COLUMNAS_EXCEL["saldo"])
        col_subtipo = _encontrar_columna(headers, COLUMNAS_EXCEL["subtipo_codigo"])
        col_tipo = _encontrar_columna(headers, COLUMNAS_EXCEL["tipo"])

        resultados = []
        for idx, row in enumerate(reader):
            try:
                fecha_str = row.get(col_fecha, "").strip() if col_fecha else ""
                fecha = _parse_fecha(fecha_str)
                if not fecha:
                    continue

                concepto = row.get(col_concepto, "").strip() if col_concepto else "Movimiento bancario"
                monto_str = row.get(col_monto, "0").strip() if col_monto else "0"
                monto = _parse_monto(monto_str)

                ref = row.get(col_ref, "").strip() or None if col_ref else None
                saldo_str = row.get(col_saldo, "").strip() if col_saldo else None
                saldo = _parse_monto(saldo_str) if saldo_str else None
                subtipo_codigo = row.get(col_subtipo, "").strip() or None if col_subtipo else None
                tipo = row.get(col_tipo, "").strip() or None if col_tipo else None

                if subtipo_codigo and subtipo_codigo.lower() in ("none", "", "null"):
                    subtipo_codigo = None

                resultados.append(MovimientoParseado(
                    fecha=fecha,
                    concepto=concepto,
                    monto=monto,
                    referencia=ref,
                    saldo=saldo,
                    tipo=tipo,
                    subtipo_codigo=subtipo_codigo,
                    idx=idx,
                    raw=row,
                ))
            except (ValueError, KeyError):
                continue

        return resultados

    @staticmethod
    def parsear_ofx(contenido: str) -> List[MovimientoParseado]:
        resultados = []
        stmt_match = re.findall(r'<STMTTRN>(.*?)</STMTTRN>', contenido, re.DOTALL)

        for idx, block in enumerate(stmt_match):
            try:
                m = re.search(r'<TRNTYPE>(.*?)[<\n]', block)
                tipo = m.group(1).strip() if m else "OTHER"

                m = re.search(r'<DTPOSTED>(.*?)[<\n]', block)
                fecha_str = m.group(1).strip()[:8] if m else None
                if not fecha_str:
                    continue
                fecha = datetime.strptime(fecha_str, "%Y%m%d").date()

                m = re.search(r'<TRNAMT>(.*?)[<\n]', block)
                monto = float(m.group(1).strip()) if m else 0

                m = re.search(r'<MEMO>(.*?)[<\n]', block)
                concepto = m.group(1).strip() if m else ""

                m = re.search(r'<FITID>(.*?)[<\n]', block)
                ref = m.group(1).strip() if m else None

                resultados.append(MovimientoParseado(
                    fecha=fecha, concepto=concepto, monto=monto,
                    referencia=ref, tipo=tipo, idx=idx,
                ))
            except (ValueError, AttributeError):
                continue

        return resultados

    @staticmethod
    def detectar_formato(archivo_nombre: str, contenido: Optional[str] = None) -> str:
        if archivo_nombre.lower().endswith('.xlsx'):
            return "xlsx"
        if archivo_nombre.lower().endswith('.xls'):
            return "xls"
        if contenido:
            if contenido.strip().startswith("OFXHEADER") or "<OFX>" in contenido:
                return "ofx"
        return "csv"

    @staticmethod
    def parsear_archivo(ruta: str, archivo_nombre: str, contenido: Optional[str] = None) -> List[MovimientoParseado]:
        fmt = CargadorService.detectar_formato(archivo_nombre, contenido)
        if fmt in ("xlsx", "xls"):
            return CargadorService.parsear_excel(ruta)
        if fmt == "ofx":
            return CargadorService.parsear_ofx(contenido or "")
        return CargadorService.parsear_csv(contenido or "")

    @staticmethod
    async def resolver_subtipos(
        db: AsyncSession,
        empresa_id: UUID,
        movimientos: List[MovimientoParseado],
    ) -> dict:
        codigos = set(m.subtipo_codigo for m in movimientos if m.subtipo_codigo)
        subtipos_map = {}

        for codigo in codigos:
            result = await db.execute(
                select(DocumentoSubtipo).where(
                    DocumentoSubtipo.company_id == empresa_id,
                    DocumentoSubtipo.codigo == codigo,
                    DocumentoSubtipo.is_active == True,
                )
            )
            sub = result.scalar_one_or_none()
            if sub:
                subtipos_map[codigo] = sub

        for m in movimientos:
            if m.subtipo_codigo and m.subtipo_codigo in subtipos_map:
                m.subtipo_id = subtipos_map[m.subtipo_codigo].id

        return {
            "encontrados": len(subtipos_map),
            "no_encontrados": len(codigos - set(subtipos_map.keys())),
        }

    @staticmethod
    async def preview_importacion(
        db: AsyncSession,
        empresa_id: UUID,
        cuenta_banco_id: UUID,
        ruta_archivo: str,
        nombre_archivo: str,
        contenido_csv: Optional[str] = None,
    ) -> dict:
        cuenta = await db.get(CuentaBanco, cuenta_banco_id)
        if not cuenta or cuenta.empresa_id != empresa_id:
            raise ValueError("Cuenta bancaria no encontrada")

        movimientos = CargadorService.parsear_archivo(ruta_archivo, nombre_archivo, contenido_csv)

        await CargadorService.resolver_subtipos(db, empresa_id, movimientos)

        existentes = await db.execute(
            select(MovimientoBanco).where(
                MovimientoBanco.empresa_id == empresa_id,
                MovimientoBanco.cuenta_id == cuenta_banco_id,
            )
        )
        hashes_existentes = set()
        for m in existentes.scalars().all():
            raw = f"{m.fecha.date() if hasattr(m.fecha, 'date') else m.fecha}|{m.concepto}|{m.entrada - m.salida}|{m.numero_documento or ''}|"
            h = hashlib.md5(raw.encode()).hexdigest()[:16]
            hashes_existentes.add(h)

        for m in movimientos:
            m.duplicado = m.hash in hashes_existentes

        total_ingresos = sum(m.monto for m in movimientos if m.es_ingreso)
        total_egresos = sum(abs(m.monto) for m in movimientos if not m.es_ingreso)

        return {
            "cuenta": {"id": str(cuenta.id), "nombre": f"{cuenta.banco} - {cuenta.numero_cuenta}"},
            "formato": CargadorService.detectar_formato(nombre_archivo, contenido_csv),
            "total_movimientos": len(movimientos),
            "duplicados": sum(1 for m in movimientos if m.duplicado),
            "total_ingresos": round(total_ingresos, 2),
            "total_egresos": round(total_egresos, 2),
            "movimientos": [m.to_dict() for m in movimientos],
        }

    @staticmethod
    async def importar_movimientos(
        db: AsyncSession,
        empresa_id: UUID,
        cuenta_banco_id: UUID,
        movimientos_data: List[dict],
        crear_conciliacion: bool = True,
        fecha_corte: Optional[date] = None,
        saldo_estado: Optional[float] = None,
    ) -> dict:
        cuenta = await db.get(CuentaBanco, cuenta_banco_id)
        if not cuenta or cuenta.empresa_id != empresa_id:
            raise ValueError("Cuenta bancaria no encontrada")

        movs_creados = []
        for data in movimientos_data:
            monto = data.get("monto", 0)
            entrada = monto if monto > 0 else 0
            salida = abs(monto) if monto < 0 else 0

            ultimo_saldo = await db.execute(
                select(MovimientoBanco.saldo).where(
                    MovimientoBanco.empresa_id == empresa_id,
                    MovimientoBanco.cuenta_id == cuenta_banco_id,
                ).order_by(MovimientoBanco.fecha.desc(), MovimientoBanco.created_at.desc()).limit(1)
            )
            ultimo = ultimo_saldo.scalar()
            saldo = (ultimo or 0) + entrada - salida

            subtipo_id = data.get("subtipo_id")
            if subtipo_id and isinstance(subtipo_id, str):
                subtipo_id = UUID(subtipo_id)

            numero_subtipo = None
            if subtipo_id:
                sub = await db.get(DocumentoSubtipo, subtipo_id)
                if sub:
                    sub.ultimo_numero = (sub.ultimo_numero or 0) + 1
                    numero_subtipo = sub.ultimo_numero

            mov = MovimientoBanco(
                empresa_id=empresa_id,
                cuenta_id=cuenta_banco_id,
                fecha=datetime.strptime(data["fecha"], "%Y-%m-%d").date() if isinstance(data["fecha"], str) else data["fecha"],
                tipo=data.get("tipo", "CREDITO" if entrada > 0 else "DEBITO"),
                numero_documento=data.get("referencia"),
                concepto=data.get("concepto", ""),
                entrada=entrada,
                salida=salida,
                saldo=saldo,
                conciliado=crear_conciliacion,
                subtipo_id=subtipo_id,
                numero_subtipo=numero_subtipo,
                origen="BANCO",
            )
            db.add(mov)
            await db.flush()
            movs_creados.append(mov)

        conciliacion_id = None
        conciliacion = None
        if crear_conciliacion:
            corte = fecha_corte or max(
                datetime.strptime(d["fecha"], "%Y-%m-%d").date() if isinstance(d["fecha"], str) else d["fecha"]
                for d in movimientos_data
            )
            saldo_est = saldo_estado or (movs_creados[-1].saldo if movs_creados else 0)
            saldo_libros = movs_creados[-1].saldo if movs_creados else 0
            dif = round(abs(saldo_est - saldo_libros), 2)

            # Find or guess period from corte date
            from app.domain.models.periodo import PeriodoContable
            per = await db.execute(
                select(PeriodoContable).where(
                    PeriodoContable.empresa_id == empresa_id,
                    PeriodoContable.fecha_inicio <= corte,
                    PeriodoContable.fecha_fin >= corte,
                )
            )
            periodo = per.scalar_one_or_none()

            conciliacion = ConciliacionBancaria(
                empresa_id=empresa_id,
                cuenta_id=cuenta_banco_id,
                periodo_id=periodo.id if periodo else None,
                fecha_inicio=(corte.replace(day=1) if periodo is None else None),
                fecha_fin=(corte if periodo is None else None),
                saldo_final_banco=saldo_est,
                saldo_final_libro=saldo_libros,
                diferencia=dif,
                estado="TEMPORAL",
            )
            db.add(conciliacion)
            await db.flush()

            for mov in movs_creados:
                partida = PartidaConciliacion(
                    conciliacion_id=conciliacion.id,
                    movimiento_banco_id=mov.id,
                    tipo="BANCO",
                    concepto=mov.concepto,
                    referencia=mov.numero_documento,
                    fecha=mov.fecha.date() if hasattr(mov.fecha, 'date') else mov.fecha,
                    monto=float(mov.entrada - mov.salida),
                    conciliado=True,
                )
                db.add(partida)
            conciliacion_id = str(conciliacion.id)

        await db.commit()

        return {
            "movimientos_creados": len(movs_creados),
            "conciliacion_id": conciliacion_id,
            "conciliacion_estado": conciliacion.estado if conciliacion else None,
        }

    @staticmethod
    async def guardar_archivo_subido(archivo_bytes: bytes, nombre: str) -> str:
        import os
        os.makedirs("/tmp/opencode/cargador", exist_ok=True)
        ruta = f"/tmp/opencode/cargador/{hashlib.md5(nombre.encode()).hexdigest()[:8]}_{nombre}"
        with open(ruta, "wb") as f:
            f.write(archivo_bytes)
        return ruta
