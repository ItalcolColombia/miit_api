import io
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class ExportacionService:
    """
    Servicio para exportar datos de reportes a diferentes formatos.
    """

    # Configuración de estilos
    HEADER_COLOR = '366092'
    HEADER_FONT_COLOR = 'FFFFFF'
    ALTERNATE_ROW_COLOR = 'F2F2F2'
    TOTALS_COLOR = 'D9E1F2'

    # Campos que deben formatearse como enteros en exportación (sin decimales)
    # Estos campos se formatearán como enteros independientemente del tipo_dato definido
    CAMPOS_ENTEROS = {
        # Nombres reales de campos (según BD)
        'transaccion_id',
        'almacen_id',
        'bascula_id',
        'consecutivo_pesada',
        # Variantes alternativas
        'id_transaccion',
        'id_almacen',
        'bascula',
        'id transaccion',
        'id transacción',
        'id almacen',
        'id almacén',
        'báscula',
        'idtransaccion',
        'idalmacen',
        'consecutivo',
    }

    # ========================================================
    # EXPORTACIÓN A EXCEL
    # ========================================================

    def exportar_excel(
            self,
            datos: List[Dict[str, Any]],
            nombre_reporte: str,
            columnas: List[Dict[str, Any]],
            totales: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Exporta datos a formato Excel (.xlsx).

        Args:
            datos: Lista de registros a exportar
            nombre_reporte: Nombre del reporte para el título
            columnas: Definición de columnas
            totales: Diccionario con totales (opcional)

        Returns:
            Contenido del archivo Excel en bytes
        """
        wb = Workbook()
        ws = wb.active
        ws.title = nombre_reporte[:31]  # Límite de Excel para nombre de hoja

        # Estilos
        header_fill = PatternFill(
            start_color=self.HEADER_COLOR,
            end_color=self.HEADER_COLOR,
            fill_type="solid"
        )
        header_font = Font(color=self.HEADER_FONT_COLOR, bold=True, size=11)
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        alternate_fill = PatternFill(
            start_color=self.ALTERNATE_ROW_COLOR,
            end_color=self.ALTERNATE_ROW_COLOR,
            fill_type="solid"
        )

        totals_fill = PatternFill(
            start_color=self.TOTALS_COLOR,
            end_color=self.TOTALS_COLOR,
            fill_type="solid"
        )
        totals_font = Font(bold=True, size=11)

        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Título del reporte
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(columnas))
        title_cell = ws.cell(row=1, column=1, value=nombre_reporte)
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center")

        # Fecha de generación
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(columnas))
        date_cell = ws.cell(
            row=2,
            column=1,
            value=f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        date_cell.font = Font(italic=True, size=10)
        date_cell.alignment = Alignment(horizontal="center")

        # Fila vacía
        start_row = 4

        # Encabezados
        for col_idx, columna in enumerate(columnas, 1):
            cell = ws.cell(row=start_row, column=col_idx, value=columna['nombre_mostrar'])
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border

        # Datos
        for row_idx, fila in enumerate(datos, start_row + 1):
            for col_idx, columna in enumerate(columnas, 1):
                valor = fila.get(columna['campo'], '')

                # Formatear valor según tipo
                valor_formateado = self._formatear_valor_excel(
                    valor,
                    columna.get('tipo_dato', 'string'),
                    columna.get('decimales', 2),
                    columna.get('campo', '')
                )

                cell = ws.cell(row=row_idx, column=col_idx, value=valor_formateado)
                cell.border = border

                # Alineación
                alineacion = columna.get('alineacion', 'left')
                cell.alignment = Alignment(horizontal=alineacion)

                # Filas alternadas
                if (row_idx - start_row) % 2 == 0:
                    cell.fill = alternate_fill

        # Fila de totales
        if totales:
            total_row = start_row + len(datos) + 1

            # Primera celda con "TOTALES"
            total_label_cell = ws.cell(row=total_row, column=1, value="TOTALES")
            total_label_cell.fill = totals_fill
            total_label_cell.font = totals_font
            total_label_cell.border = border

            for col_idx, columna in enumerate(columnas, 1):
                campo = columna['campo']
                if campo in totales:
                    valor = totales[campo]
                    valor_formateado = self._formatear_valor_excel(
                        valor,
                        columna.get('tipo_dato', 'number'),
                        columna.get('decimales', 2),
                        campo
                    )
                    cell = ws.cell(row=total_row, column=col_idx, value=valor_formateado)
                else:
                    cell = ws.cell(row=total_row, column=col_idx, value="")

                cell.fill = totals_fill
                cell.font = totals_font
                cell.border = border

                alineacion = columna.get('alineacion', 'left')
                cell.alignment = Alignment(horizontal=alineacion)

        # Ajustar ancho de columnas
        for col_idx, columna in enumerate(columnas, 1):
            # Calcular ancho basado en contenido
            max_length = len(str(columna['nombre_mostrar']))

            for fila in datos[:100]:  # Solo revisar primeras 100 filas
                valor = fila.get(columna['campo'], '')
                if valor:
                    max_length = max(max_length, len(str(valor)))

            # Limitar ancho
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = adjusted_width

        # Congelar encabezados
        ws.freeze_panes = ws.cell(row=start_row + 1, column=1)

        # Guardar en memoria
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        return excel_file.getvalue()

    def _formatear_valor_excel(
            self,
            valor: Any,
            tipo_dato: str,
            decimales: int = 2,
            campo: str = ''
    ) -> Any:
        """
        Formatea un valor para Excel según su tipo.

        Args:
            valor: Valor a formatear
            tipo_dato: Tipo de dato de la columna
            decimales: Número de decimales para números
            campo: Nombre del campo (para detectar campos enteros)
        """
        if valor is None:
            return ""

        # Verificar si es un campo que debe ser entero
        campo_lower = campo.lower() if campo else ''
        es_campo_entero = campo_lower in self.CAMPOS_ENTEROS or tipo_dato == 'integer'

        if es_campo_entero:
            try:
                return int(float(valor))
            except (ValueError, TypeError):
                return valor

        if tipo_dato == 'number':
            try:
                return round(float(valor), decimales)
            except (ValueError, TypeError):
                return valor

        elif tipo_dato in ('date', 'datetime'):
            if isinstance(valor, datetime):
                return valor
            elif isinstance(valor, str):
                try:
                    return datetime.fromisoformat(valor.replace('Z', '+00:00'))
                except:
                    return valor

        return valor

    # ========================================================
    # EXPORTACIÓN A PDF
    # ========================================================

    def exportar_pdf(
            self,
            datos: List[Dict[str, Any]],
            nombre_reporte: str,
            columnas: List[Dict[str, Any]],
            totales: Optional[Dict[str, Any]] = None,
            orientacion: str = 'auto'
    ) -> bytes:
        """
        Exporta datos a formato PDF optimizado para reportes con muchas columnas.

        Args:
            datos: Lista de registros a exportar
            nombre_reporte: Nombre del reporte
            columnas: Definición de columnas
            totales: Diccionario con totales (opcional)
            orientacion: 'portrait', 'landscape' o 'auto' (detecta automáticamente)

        Returns:
            Contenido del archivo PDF en bytes
        """
        buffer = io.BytesIO()

        num_columnas = len(columnas)

        # Determinar orientación según número de columnas si es 'auto'
        if orientacion == 'auto':
            if num_columnas > 6:
                orientacion = 'landscape'
            else:
                orientacion = 'portrait'

        # Configurar página
        if orientacion == 'landscape':
            pagesize = landscape(A4)
        else:
            pagesize = A4

        # Ajustar márgenes según número de columnas
        if num_columnas > 10:
            margins = 0.3 * cm
        elif num_columnas > 7:
            margins = 0.5 * cm
        else:
            margins = 1 * cm

        doc = SimpleDocTemplate(
            buffer,
            pagesize=pagesize,
            rightMargin=margins,
            leftMargin=margins,
            topMargin=1 * cm,
            bottomMargin=1 * cm
        )

        elements = []
        styles = getSampleStyleSheet()

        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14 if num_columnas <= 8 else 12,
            alignment=TA_CENTER,
            spaceAfter=8
        )

        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.gray,
            spaceAfter=12
        )

        # Título
        elements.append(Paragraph(f"Informe de {nombre_reporte}", title_style))

        # Fecha de generación
        fecha_generacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elements.append(Paragraph(f"Generado: {fecha_generacion}", date_style))

        # Todas las columnas visibles
        columnas_visibles = columnas

        # Determinar tamaño de fuente según número de columnas
        if num_columnas > 12:
            font_size_header = 6
            font_size_body = 5
            max_chars = 15
        elif num_columnas > 10:
            font_size_header = 7
            font_size_body = 6
            max_chars = 20
        elif num_columnas > 8:
            font_size_header = 8
            font_size_body = 7
            max_chars = 25
        elif num_columnas > 6:
            font_size_header = 9
            font_size_body = 8
            max_chars = 30
        else:
            font_size_header = 10
            font_size_body = 9
            max_chars = 40

        table_data = []

        # Encabezados - truncar si son muy largos
        headers = []
        for col in columnas_visibles:
            header_text = col['nombre_mostrar']
            if len(header_text) > max_chars:
                header_text = header_text[:max_chars-2] + '..'
            headers.append(header_text)
        table_data.append(headers)

        # Datos - truncar texto largo
        for fila in datos:
            row = []
            for col in columnas_visibles:
                valor = fila.get(col['campo'], '')
                valor_formateado = self._formatear_valor_pdf(
                    valor,
                    col.get('tipo_dato', 'string'),
                    col.get('decimales', 2),
                    col.get('sufijo', ''),
                    col.get('campo', '')
                )
                # Truncar si es muy largo
                if isinstance(valor_formateado, str) and len(valor_formateado) > max_chars:
                    valor_formateado = valor_formateado[:max_chars-3] + '...'
                row.append(valor_formateado)
            table_data.append(row)

        # Fila de totales
        if totales:
            total_row = ['TOTALES']
            for col in columnas_visibles[1:]:
                campo = col['campo']
                if campo in totales:
                    valor = totales[campo]
                    valor_formateado = self._formatear_valor_pdf(
                        valor,
                        col.get('tipo_dato', 'number'),
                        col.get('decimales', 2),
                        col.get('sufijo', ''),
                        campo
                    )
                    total_row.append(valor_formateado)
                else:
                    total_row.append('')
            table_data.append(total_row)

        # Calcular anchos de columna dinámicamente
        available_width = pagesize[0] - (2 * margins)
        col_widths = self._calcular_anchos_columnas(
            columnas_visibles,
            datos,
            available_width,
            max_chars
        )

        # Crear tabla
        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Estilos de tabla
        style = TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(f'#{self.HEADER_COLOR}')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), font_size_header),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4 if num_columnas > 8 else 6),
            ('TOPPADDING', (0, 0), (-1, 0), 4 if num_columnas > 8 else 6),

            # Cuerpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), font_size_body),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2 if num_columnas > 8 else 4),
            ('TOPPADDING', (0, 1), (-1, -1), 2 if num_columnas > 8 else 4),

            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),

            # Línea gruesa debajo del encabezado
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor(f'#{self.HEADER_COLOR}')),
        ])

        # Filas alternadas
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor(f'#{self.ALTERNATE_ROW_COLOR}'))

        # Fila de totales
        if totales:
            last_row = len(table_data) - 1
            style.add('BACKGROUND', (0, last_row), (-1, last_row), colors.HexColor(f'#{self.TOTALS_COLOR}'))
            style.add('FONTNAME', (0, last_row), (-1, last_row), 'Helvetica-Bold')

        # Alineación por tipo de columna
        for col_idx, col in enumerate(columnas_visibles):
            alineacion = col.get('alineacion', 'left')
            if alineacion == 'right':
                style.add('ALIGN', (col_idx, 1), (col_idx, -1), 'RIGHT')
            elif alineacion == 'center':
                style.add('ALIGN', (col_idx, 1), (col_idx, -1), 'CENTER')
            else:
                style.add('ALIGN', (col_idx, 1), (col_idx, -1), 'LEFT')

        table.setStyle(style)
        elements.append(table)

        # Pie de página con total de registros
        elements.append(Spacer(1, 12))
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray
        )
        elements.append(Paragraph(f"Total de registros: {len(datos)}", footer_style))

        # Construir PDF
        doc.build(elements)

        buffer.seek(0)
        return buffer.getvalue()

    def _calcular_anchos_columnas(
            self,
            columnas: List[Dict[str, Any]],
            datos: List[Dict[str, Any]],
            page_width: float,
            max_chars: int
    ) -> List[float]:
        """
        Calcula anchos de columna basados en el contenido.

        Args:
            columnas: Definición de columnas
            datos: Datos del reporte
            page_width: Ancho disponible de la página
            max_chars: Máximo de caracteres permitidos

        Returns:
            Lista de anchos de columna
        """
        num_cols = len(columnas)

        # Ancho mínimo y máximo por columna
        min_width = 1.2 * cm
        max_width = 5 * cm

        # Calcular ancho basado en el header y algunos datos
        widths = []
        sample_size = min(50, len(datos))  # Muestra para calcular anchos

        for col in columnas:
            campo = col.get('campo', '')
            header = col.get('nombre_mostrar', campo)

            # Ancho del header (truncado)
            header_len = min(len(str(header)), max_chars)
            max_len = header_len

            # Revisar datos de muestra
            for row in datos[:sample_size]:
                valor = row.get(campo, '')
                if valor:
                    valor_len = min(len(str(valor)), max_chars)
                    max_len = max(max_len, valor_len)

            # Convertir caracteres a puntos (aproximado)
            estimated_width = max_len * 0.22 * cm

            # Aplicar límites
            width = max(min_width, min(max_width, estimated_width))
            widths.append(width)

        # Ajustar para que quepan en la página
        total_width = sum(widths)
        if total_width > page_width:
            scale = page_width / total_width
            widths = [w * scale for w in widths]
        elif total_width < page_width * 0.9:
            # Si sobra mucho espacio, distribuir proporcionalmente
            scale = (page_width * 0.95) / total_width
            widths = [w * scale for w in widths]

        return widths

    def _formatear_valor_pdf(
            self,
            valor: Any,
            tipo_dato: str,
            decimales: int = 2,
            sufijo: str = '',
            campo: str = ''
    ) -> str:
        """
        Formatea un valor para PDF.

        Args:
            valor: Valor a formatear
            tipo_dato: Tipo de dato de la columna
            decimales: Número de decimales para números
            sufijo: Sufijo a agregar al valor (ej: unidad de medida)
            campo: Nombre del campo (para detectar campos enteros)
        """
        if valor is None:
            return '-'

        # Verificar si es un campo que debe ser entero
        campo_lower = campo.lower() if campo else ''
        es_campo_entero = campo_lower in self.CAMPOS_ENTEROS or tipo_dato == 'integer'


        if es_campo_entero:
            try:
                numero = int(float(valor))
                formateado = f"{numero:,}"
                if sufijo:
                    formateado = f"{formateado} {sufijo}"
                return formateado
            except (ValueError, TypeError):
                return str(valor)

        if tipo_dato == 'number':
            try:
                numero = float(valor)
                formateado = f"{numero:,.{decimales}f}"
                if sufijo:
                    formateado = f"{formateado} {sufijo}"
                return formateado
            except (ValueError, TypeError):
                return str(valor)

        elif tipo_dato == 'date':
            if isinstance(valor, datetime):
                return valor.strftime('%Y-%m-%d')
            elif isinstance(valor, str):
                try:
                    dt = datetime.fromisoformat(valor.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%d')
                except:
                    return valor

        elif tipo_dato == 'datetime':
            if isinstance(valor, datetime):
                return valor.strftime('%Y-%m-%d %H:%M')
            elif isinstance(valor, str):
                try:
                    dt = datetime.fromisoformat(valor.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%d %H:%M')
                except:
                    return valor

        return str(valor) if valor else '-'

    # ========================================================
    # EXPORTACIÓN A CSV
    # ========================================================

    def exportar_csv(
            self,
            datos: List[Dict[str, Any]],
            columnas: List[Dict[str, Any]]
    ) -> str:
        """
        Exporta datos a formato CSV.

        Args:
            datos: Lista de registros a exportar
            columnas: Definición de columnas

        Returns:
            Contenido del archivo CSV como string
        """
        # Crear DataFrame con las columnas en el orden correcto
        campos = [col['campo'] for col in columnas]
        nombres = {col['campo']: col['nombre_mostrar'] for col in columnas}

        # Extraer solo los campos definidos
        datos_filtrados = []
        for fila in datos:
            fila_filtrada = {campo: fila.get(campo, '') for campo in campos}
            datos_filtrados.append(fila_filtrada)

        df = pd.DataFrame(datos_filtrados)

        # Reordenar columnas
        df = df[campos]

        # Renombrar columnas
        df.rename(columns=nombres, inplace=True)

        # Formatear valores
        for col in columnas:
            campo = col['campo']
            nombre = col['nombre_mostrar']
            tipo = col.get('tipo_dato', 'string')

            if nombre in df.columns:
                # Verificar si es un campo que debe ser entero
                campo_lower = campo.lower()
                es_campo_entero = campo_lower in self.CAMPOS_ENTEROS or tipo == 'integer'


                if es_campo_entero:
                    df[nombre] = df[nombre].apply(
                        lambda x: self._formatear_entero_csv(x)
                    )
                elif tipo == 'datetime':
                    df[nombre] = df[nombre].apply(
                        lambda x: self._formatear_datetime_csv(x)
                    )
                elif tipo == 'date':
                    df[nombre] = df[nombre].apply(
                        lambda x: self._formatear_date_csv(x)
                    )

        # Convertir a CSV
        return df.to_csv(index=False, encoding='utf-8')

    def _formatear_datetime_csv(self, valor: Any) -> str:
        """Formatea datetime para CSV."""
        if valor is None:
            return ''
        if isinstance(valor, datetime):
            return valor.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(valor, str):
            try:
                dt = datetime.fromisoformat(valor.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                return valor
        return str(valor) if valor else ''

    def _formatear_date_csv(self, valor: Any) -> str:
        """Formatea date para CSV."""
        if valor is None:
            return ''
        if isinstance(valor, datetime):
            return valor.strftime('%Y-%m-%d')
        elif isinstance(valor, str):
            try:
                dt = datetime.fromisoformat(valor.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except:
                return valor
        return str(valor) if valor else ''

    def _formatear_entero_csv(self, valor: Any) -> str:
        """
        Formatea un valor como entero para CSV (sin decimales).

        Args:
            valor: Valor a formatear

        Returns:
            Valor formateado como entero (string)
        """
        if valor is None:
            return ''
        try:
            return str(int(float(valor)))
        except (ValueError, TypeError):
            return str(valor) if valor else ''
