import uuid
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import Optional

from fpdf import FPDF
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.cheque import Cheque, ChequeFormato, Chequera
from app.domain.models.banco import CuentaBanco
from app.domain.models.proveedor import Proveedor
from app.domain.models.empresa import Empresa


class ChequePrintService:
    """Generates cheque print layouts: HTML, PDF, or dot-matrix text."""

    UNIDADES = (
        'CERO', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE'
    )
    DECENAS = (
        'DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS',
        'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE'
    )
    DECENAS_DEC = (
        '', 'DIEZ', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA',
        'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA'
    )
    CENTENAS = (
        '', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS',
        'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS'
    )

    _MONEDA_SINGULAR = 'CÓRDOBA'
    _MONEDA_PLURAL = 'CÓRDOBAS'

    @classmethod
    def numero_a_letras(cls, monto: Decimal, moneda: str | None = None) -> str:
        if moneda is None:
            moneda_s = cls._MONEDA_SINGULAR
            moneda_p = cls._MONEDA_PLURAL
        else:
            moneda_s = moneda
            moneda_p = moneda

        entero = int(monto)
        decimales = int(round((monto - entero) * 100))

        letras_entero = cls._convertir_entero(entero)
        if entero == 1:
            parte_monetaria = f"{letras_entero} {moneda_s}"
        else:
            parte_monetaria = f"{letras_entero} {moneda_p}" if letras_entero else f"CERO {moneda_p}"

        if decimales > 0:
            return f"{parte_monetaria} CON {decimales:02d}/100"
        return f"{parte_monetaria} CON 00/100"

    @classmethod
    def _convertir_entero(cls, n: int) -> str:
        if n == 0:
            return 'CERO'
        if n < 10:
            return cls.UNIDADES[n]
        if n < 20:
            return cls.DECENAS[n - 10]
        if n < 100:
            d = n // 10
            u = n % 10
            if u == 0:
                return cls.DECENAS_DEC[d]
            return f"{cls.DECENAS_DEC[d]} Y {cls.UNIDADES[u]}".replace('VEINTE Y ', 'VEINTI')
        if n < 1000:
            c = n // 100
            resto = n % 100
            if n == 100:
                return 'CIEN'
            if resto == 0:
                return cls.CENTENAS[c]
            return f"{cls.CENTENAS[c]} {cls._convertir_entero(resto)}"
        if n < 1_000_000:
            m = n // 1000
            resto = n % 1000
            if m == 1:
                miles = 'MIL'
            else:
                miles = f"{cls._convertir_entero(m)} MIL"
            if resto == 0:
                return miles
            return f"{miles} {cls._convertir_entero(resto)}"
        if n < 1_000_000_000:
            mm = n // 1_000_000
            resto = n % 1_000_000
            if mm == 1:
                millones = 'UN MILLÓN'
            else:
                millones = f"{cls._convertir_entero(mm)} MILLONES"
            if resto == 0:
                return millones
            return f"{millones} {cls._convertir_entero(resto)}"
        return str(n)

    # ── Format resolver ──

    async def _get_formato(self, db: AsyncSession, cheque: Cheque, formato_id: uuid.UUID | None = None) -> ChequeFormato | None:
        if formato_id:
            return await db.get(ChequeFormato, formato_id)
        # Try from account config
        cuenta = await db.get(CuentaBanco, cheque.cuenta_bancaria_id)
        if cuenta and cuenta.cheque_formato_id:
            return await db.get(ChequeFormato, cuenta.cheque_formato_id)
        # Fallback to active format for company
        r = await db.execute(
            select(ChequeFormato).where(
                ChequeFormato.empresa_id == cheque.empresa_id,
                ChequeFormato.activo == True,
            ).limit(1)
        )
        return r.scalar_one_or_none()

    def _collect_fields(self, cheque: Cheque, formato: ChequeFormato | None):
        """Extract field values and positions from a cheque and format config."""
        fmt_str = formato.campo_fecha_formato if formato else 'DD/MM/YYYY'
        fecha_str = cheque.fecha.strftime(self._fmt_to_python(fmt_str))
        monto_letras = self.numero_a_letras(cheque.monto, 'CÓRDOBAS')

        return [
            ('fecha', fecha_str, float(formato.campo_fecha_x if formato else 130), float(formato.campo_fecha_y if formato else 14)),
            ('numero', f"Cheque No. {cheque.numero}", float(formato.campo_fecha_x if formato else 130) - 80, float(formato.campo_fecha_y if formato else 14) - 10),
            ('pagadero', cheque.pagadero_a, float(formato.campo_pagadero_x if formato else 25), float(formato.campo_pagadero_y if formato else 28)),
            ('monto_num', f"C$ {cheque.monto:,.2f}", float(formato.campo_monto_num_x if formato else 130), float(formato.campo_monto_num_y if formato else 28)),
            ('monto_letras', monto_letras, float(formato.campo_monto_letras_x if formato else 25), float(formato.campo_monto_letras_y if formato else 42)),
            ('concepto', cheque.concepto or '', float(formato.campo_concepto_x if formato else 25), float(formato.campo_concepto_y if formato else 56)),
            ('firma', '________________________', float(formato.campo_firma_x if formato else 25), float(formato.campo_firma_y if formato else 72)),
        ]

    # ── PDF generation ──

    async def generar_pdf(
        self,
        db: AsyncSession,
        cheque_id: uuid.UUID,
        formato_id: uuid.UUID | None = None,
    ) -> bytes:
        """Genera PDF listo para imprimir, con posicionamiento exacto desde ChequeFormato."""
        cheque = await db.get(Cheque, cheque_id)
        if not cheque:
            raise ValueError("Cheque no encontrado")

        formato = await self._get_formato(db, cheque, formato_id)
        ancho_mm = float(formato.ancho_mm) if formato else 216.0
        alto_mm = float(formato.alto_mm) if formato else 89.0
        fsize = formato.fuente_tamano if formato else 11
        fname = formato.fuente_nombre if formato else 'Courier New'

        pdf = FPDF(unit='mm', format=(ancho_mm, alto_mm))
        pdf.add_page()

        # Try to use a built-in monospace font; fallback to Helvetica
        try:
            pdf.add_font('Cheque', '', '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf', uni=True)
            pdf.add_font('Cheque', 'B', '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf', uni=True)
            font_family = 'Cheque'
        except Exception:
            # Courier is available as a core PDF font
            font_family = 'Courier'

        pdf.set_font(font_family, '', fsize)
        pdf.set_auto_page_break(auto=False)

        fields = self._collect_fields(cheque, formato)
        for name, value, x_mm, y_mm in fields:
            w_mm = None
            if name == 'fecha':
                w_mm = 30
            elif name == 'numero':
                w_mm = 60
            elif name == 'monto_num':
                w_mm = 40
            elif name in ('pagadero', 'monto_letras', 'concepto'):
                w_mm = 80
            elif name == 'firma':
                w_mm = 50

            if w_mm:
                # Set position and write within a cell
                pdf.set_xy(x_mm, y_mm)
                pdf.cell(w_mm, 6, value)
            else:
                pdf.set_xy(x_mm, y_mm)
                pdf.cell(0, 6, value)

        return bytes(pdf.output())

    # ── HTML generation ──

    async def generar_html_impresion(
        self,
        db: AsyncSession,
        cheque_id: uuid.UUID,
        formato_id: uuid.UUID | None = None,
    ) -> str:
        cheque = await db.get(Cheque, cheque_id)
        if not cheque:
            raise ValueError("Cheque no encontrado")

        formato = await self._get_formato(db, cheque, formato_id)
        ancho_mm = float(formato.ancho_mm) if formato else 216.0
        alto_mm = float(formato.alto_mm) if formato else 89.0
        fsize = formato.fuente_tamano if formato else 11
        fname = formato.fuente_nombre if formato else 'Courier New'

        def mm_to_cm(val: float) -> str:
            return f"{val / 10:.1f}cm"

        def field_style(x: float, y: float, w: str = 'auto') -> str:
            return (
                f"position: absolute; left: {mm_to_cm(x)}; top: {mm_to_cm(y)}; width: {w}; "
                f"font-family: '{fname}', monospace; font-size: {fsize}pt;"
            )

        fields = self._collect_fields(cheque, formato)

        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  @page {{ size: {ancho_mm:.1f}mm {alto_mm:.1f}mm; margin: 0; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: {ancho_mm:.1f}mm; height: {alto_mm:.1f}mm; position: relative;
    font-family: '{fname}', monospace; font-size: {fsize}pt; overflow: hidden;
  }}
  .campo {{ position: absolute; }}
</style>
</head><body>
"""
        for name, value, x, y in fields:
            w = 'auto'
            if name == 'fecha': w = '30mm'
            elif name == 'numero': w = '60mm'
            elif name == 'monto_num': w = '40mm'
            elif name in ('pagadero', 'monto_letras', 'concepto'): w = '80mm'
            elif name == 'firma': w = '50mm'
            html += f"""  <div class="campo" style="{field_style(x, y, w)}">{value}</div>\n"""

        html += "</body></html>"
        return html

    # ── Dot-matrix text ──

    async def generar_texto_matricial(
        self,
        db: AsyncSession,
        cheque_id: uuid.UUID,
    ) -> str:
        cheque = await db.get(Cheque, cheque_id)
        if not cheque:
            raise ValueError("Cheque no encontrado")

        formato = await self._get_formato(db, cheque)

        def mm_to_col(x_mm: float) -> int:
            return max(0, min(131, int(x_mm * 0.394)))

        def mm_to_line(y_mm: float) -> int:
            return max(0, int(y_mm / 4.23))

        grid = [[' ' for _ in range(132)] for _ in range(66)]

        def write_at(text: str, x_mm: float, y_mm: float):
            col = mm_to_col(x_mm)
            row = mm_to_line(y_mm)
            if row >= 66:
                return
            for i, ch in enumerate(text):
                if col + i < 132:
                    grid[row][col + i] = ch

        fields = self._collect_fields(cheque, formato)
        for name, value, x, y in fields:
            write_at(value, x, y)

        lines = [''.join(row).rstrip() for row in grid]
        while lines and not lines[-1].strip():
            lines.pop()
        return '\n'.join(lines)

    def _fmt_to_python(self, fmt: str) -> str:
        return (
            fmt.replace('DD', '%d')
            .replace('MM', '%m')
            .replace('YYYY', '%Y')
            .replace('YY', '%y')
        )

    async def marcar_impreso(self, db: AsyncSession, cheque_id: uuid.UUID):
        cheque = await db.get(Cheque, cheque_id)
        if cheque:
            cheque.impreso = True
            cheque.veces_impreso = (cheque.veces_impreso or 0) + 1
            await db.commit()
